"""
CV Parser Service - Extract structured data from CV/Resume PDFs using free LLMs.

Uses Open Router (Llama 3.1 70B) as primary parser with Gemini Flash as fallback.
Combines OCR text extraction with LLM-based structuring.

Supported formats: PDF, DOCX (via OCR)
Output: ExtractedData model (JSON structure)
"""
import os
import re
import json
import logging
import hashlib
from typing import Tuple, Optional, Dict, Any
import pdfplumber
from io import BytesIO

# LLM clients
import openai  # For Open Router
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-genai not installed, Gemini fallback disabled")

from models.schemas import ExtractedData
from services.chandra_ocr_service import ChandraOCRService

logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Open Router endpoint
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model selection
# Open Router models - NO :free suffix (that was the issue!)
PRIMARY_MODEL = "meta-llama/llama-3-8b-instruct"  # Working model, no :free needed
FALLBACK_MODEL_OR = "mistralai/mistral-7b-instruct"  # Secondary option
GEMINI_MODEL = "models/gemini-2.5-flash"  # Gemini with NEW API (models/ prefix required)


class CVParserService:
    """
    Parse CV/Resume PDFs into structured ExtractedData format.
    
    Pipeline:
    1. PDF → Text extraction (pdfplumber or OCR fallback)
    2. Text → Structured JSON (LLM: Open Router → Gemini fallback)
    3. JSON → ExtractedData validation
    
    Features:
    - Multiple free LLM options
    - Intelligent fallback strategy
    - Robust error handling
    - Generates unique candidate IDs
    """
    
    def __init__(self):
        """Initialize CV parser with LLM clients."""
        self.ocr_service = ChandraOCRService()
        
        # Initialize Open Router client
        if OPENROUTER_API_KEY:
            self.openrouter_client = openai.OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=OPENROUTER_API_KEY
            )
            logger.info("✓ Open Router client initialized")
        else:
            self.openrouter_client = None
            logger.warning("⚠ OPENROUTER_API_KEY not set, Open Router disabled")
        
        # Initialize Gemini client (NEW google-genai package)
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("✓ Gemini client initialized (new API)")
        else:
            self.gemini_client = None
            if not GEMINI_API_KEY:
                logger.warning("⚠ GEMINI_API_KEY not set, Gemini fallback disabled")
    
    async def parse_cv_pdf(self, pdf_bytes: bytes, filename: str = "resume.pdf") -> ExtractedData:
        """
        Parse CV PDF into structured ExtractedData.
        
        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename (for logging)
            
        Returns:
            ExtractedData model with extracted CV information
            
        Raises:
            Exception: If all parsing methods fail
        """
        logger.info(f"📄 Parsing CV: {filename} ({len(pdf_bytes)} bytes)")
        
        # Step 1: Extract text from PDF
        cv_text = await self._extract_text(pdf_bytes, filename)
        
        if not cv_text or len(cv_text.strip()) < 100:
            raise ValueError(f"Insufficient text extracted from CV: {len(cv_text)} chars")
        
        logger.info(f"✓ Extracted {len(cv_text)} characters of text")
        
        # Step 2: Structure with LLM (with fallback chain)
        structured_data = await self._structure_with_llm(cv_text, filename)
        
        # Step 3: Validate and convert to ExtractedData
        extracted_data = self._validate_and_convert(structured_data, filename)
        
        logger.info(f"✓ CV parsed successfully: {extracted_data.candidate_id}")
        return extracted_data
    
    async def _extract_text(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Extract text from PDF using pdfplumber (fast) or OCR (fallback).
        
        Args:
            pdf_bytes: Raw PDF bytes
            filename: Filename for logging
            
        Returns:
            Extracted text string
        """
        # Try pdfplumber first (fast, works for native PDFs)
        try:
            logger.info("Attempting text extraction with pdfplumber...")
            text = self._extract_with_pdfplumber(pdf_bytes)
            
            if text and len(text.strip()) > 100:
                logger.info("✓ pdfplumber extraction successful")
                return text
            else:
                logger.warning(f"pdfplumber extracted insufficient text ({len(text)} chars), trying OCR...")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, falling back to OCR...")
        
        # Fallback to OCR (works for scanned PDFs)
        try:
            logger.info("Attempting OCR extraction...")
            text, metadata = await self.ocr_service.process_upload(
                pdf_bytes, 
                "application/pdf", 
                filename
            )
            logger.info(f"✓ OCR extraction successful: {metadata.get('method', 'unknown')}")
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise ValueError(f"Failed to extract text from CV: {e}")
    
    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> str:
        """
        Extract text using pdfplumber (fast, for native PDFs).
        
        Args:
            pdf_bytes: Raw PDF bytes
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    logger.debug(f"Page {page_num}: extracted {len(page_text)} chars")
        
        return "\n\n".join(text_parts)
    
    async def _structure_with_llm(self, cv_text: str, filename: str) -> Dict[str, Any]:
        """
        Structure CV text into JSON using LLM with fallback chain.
        
        Fallback order:
        1. Open Router Llama 3.1 70B (best quality)
        2. Open Router Llama 3.1 8B (faster)
        3. Google Gemini Flash (reliable)
        
        Args:
            cv_text: Extracted CV text
            filename: Filename for logging
            
        Returns:
            Structured JSON dictionary
        """
        errors = []
        
        # Try Open Router Llama 70B (primary)
        if self.openrouter_client:
            try:
                logger.info(f"Structuring with Open Router ({PRIMARY_MODEL})...")
                return await self._parse_with_openrouter(cv_text, PRIMARY_MODEL)
            except Exception as e:
                error_msg = f"Open Router 70B failed: {str(e)[:100]}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
                # Try Open Router Llama 8B (faster fallback)
                try:
                    logger.info(f"Retrying with faster model ({FALLBACK_MODEL_OR})...")
                    return await self._parse_with_openrouter(cv_text, FALLBACK_MODEL_OR)
                except Exception as e2:
                    error_msg = f"Open Router 8B failed: {str(e2)[:100]}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
        
        # Fallback to Gemini
        if self.gemini_client:
            try:
                logger.info("Falling back to Gemini 2.5 Flash...")
                return await self._parse_with_gemini(cv_text)
            except Exception as e:
                error_msg = f"Gemini failed: {str(e)[:100]}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # All methods failed
        raise Exception(f"All LLM parsing methods failed: {'; '.join(errors)}")
    
    async def _parse_with_openrouter(self, cv_text: str, model: str) -> Dict[str, Any]:
        """
        Parse CV using Open Router API.
        
        Args:
            cv_text: CV text to parse
            model: Model identifier (e.g., "meta-llama/llama-3.1-70b-instruct:free")
            
        Returns:
            Structured JSON dictionary
        """
        prompt = self._get_extraction_prompt()
        
        response = self.openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"CV Text:\n\n{cv_text}"}
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=4000,  # Enough for detailed CV data
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response (handle markdown code blocks)
        json_str = self._extract_json_from_response(content)
        
        logger.info(f"✓ Open Router ({model.split('/')[1][:20]}) structured successfully")
        return json.loads(json_str)
    
    async def _parse_with_gemini(self, cv_text: str) -> Dict[str, Any]:
        """
        Parse CV using Google Gemini 2.5 Flash (NEW google-genai API).
        
        Args:
            cv_text: CV text to parse
            
        Returns:
            Structured JSON dictionary
        """
        prompt = self._get_extraction_prompt()
        full_prompt = f"{prompt}\n\nCV Text:\n\n{cv_text}"
        
        response = self.gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt
        )
        
        # Extract JSON from response
        json_str = self._extract_json_from_response(response.text)
        
        logger.info("✓ Gemini 2.5 Flash structured successfully")
        return json.loads(json_str)
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response (handles markdown code blocks).
        
        Args:
            response: Raw LLM response
            
        Returns:
            Clean JSON string
        """
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # Return as-is and let json.loads() handle it
        return response.strip()
    
    def _get_extraction_prompt(self) -> str:
        """
        Get the system prompt for CV extraction.
        
        Returns:
            Prompt string with JSON schema
        """
        return """You are a CV/Resume parser. Extract structured data from the provided CV text and return ONLY valid JSON.

**Required JSON Schema:**
{
  "candidate_name": "Full name (REQUIRED)",
  "email": "Email address (or null if not found)",
  "mobile_number": "Phone number (or null if not found)",
  "current_role": "Current job title (or null)",
  "target_role": "Desired/Target role (infer from summary/objective, or null)",
  "current_employment": "Current company name (or null)",
  "education": {
    "degree": "Highest degree (e.g., 'BSc Computer Science')",
    "university": "University name"
  },
  "skills": [{
    "programming_languages": ["Python", "Java", "JavaScript", "C++", "Kotlin", "PHP", "TypeScript", ...],
    "frameworks": ["React", "Django", "TensorFlow", "PyTorch", "Flask", "Spring Boot", "Express.js", ...],
    "web_technologies": ["HTML", "CSS", "Node.js", "Tailwind CSS", "Bootstrap", "Sass", "jQuery", ...],
    "database": ["MySQL", "PostgreSQL", "MongoDB", "SQL", "Redis", "Oracle", ...],
    "tools": ["Git", "GitHub", "Figma", "MS Excel", "Power BI", "Tableau", "Android Studio", "Visual Studio", "Jupyter", "Streamlit", ...],
    "operating_systems": ["Windows", "Linux", "macOS", "Unix", "Ubuntu", ...],
    "technologies": ["Docker", "AWS", "Azure", "Elasticsearch", "Prophet", "XGBoost", "Kubernetes", "Jenkins", ...],
    "technical_skills": ["Machine Learning", "Data Analysis", "Data Science", "Predictive Analytics", "Data Visualization", "Mobile Development", "Web Development", "Cloud Computing", ...],
    "soft_skills": ["Leadership", "Communication", "Teamwork", "Problem Solving", ...]
  }],
  "projects_and_technologies_involved": [{
    "project_name": "Project title",
    "project_description": "Brief description (or null)",
    "duration": "Time period (e.g., 'Jan 2024 – Mar 2024') (or null)",
    "complexity": "High|Medium|Low (infer from description, or null)",
    "technologies_used": ["Python", "TensorFlow", ...]
  }],
  "certificates_or_qualifications": ["AWS Certified", "PMP", ...],
  "experience_months": 24,  // Calculate from work history
  "num_projects": 3  // Count of projects
}

**Extraction Rules:**
1. Extract contact info (name, email, phone) from header/top section
2. Identify current role from most recent work experience
3. Infer target role from objective/summary or senior version of current role
4. **EXTRACT EVERY SINGLE SKILL** mentioned in the resume - do not skip anything technical
5. Categorize skills into the correct category:
   - **programming_languages**: Core languages (Python, Java, JavaScript, C++, PHP, Kotlin, TypeScript, Ruby, Go, etc.)
   - **frameworks**: Software frameworks (React, Django, TensorFlow, PyTorch, Flask, Spring Boot, Express.js, Angular, Vue.js, etc.)
   - **web_technologies**: Web-specific tech (HTML, CSS, Node.js, Tailwind CSS, Bootstrap, Sass, jQuery, Ajax, REST API, GraphQL, etc.)
   - **database**: All database systems (MySQL, PostgreSQL, MongoDB, SQL, Redis, Oracle, Cassandra, Neo4j, etc.)
   - **tools**: Development and productivity tools (Git, GitHub, Figma, MS Excel, Power BI, Tableau, Jira, Android Studio, Visual Studio, Jupyter Notebook, Streamlit, Postman, etc.)
   - **operating_systems**: Operating systems (Windows, Linux, macOS, Unix, Ubuntu, CentOS, Android, iOS, etc.)
   - **technologies**: Cloud, DevOps, and other tech (Docker, AWS, Azure, GCP, Elasticsearch, Kubernetes, Jenkins, CI/CD, Kafka, etc.)
   - **technical_skills**: Broad technical competencies (Machine Learning, Deep Learning, Data Analysis, Data Science, Predictive Analytics, Data Visualization, Mobile Development, Web Development, Cloud Computing, etc.)
6. Extract ALL projects with technologies used
7. Count total experience in months across all jobs
8. If field not found, use null (not empty string)
9. Return ONLY the JSON object, no markdown formatting or explanation

**CRITICAL**: If you see a skill and are unsure which category, still include it in the most relevant category. DO NOT skip any skills!

**IMPORTANT:** Return ONLY valid JSON. Do not include any text before or after the JSON object."""
    
    def _validate_and_convert(self, structured_data: Dict[str, Any], filename: str) -> ExtractedData:
        """
        Validate and convert structured JSON to ExtractedData model.
        
        Args:
            structured_data: Raw JSON from LLM
            filename: Original filename
            
        Returns:
            Validated ExtractedData instance
        """
        # Generate unique candidate ID if not provided
        if not structured_data.get("candidate_id"):
            # Generate ID from name + email + timestamp
            name = structured_data.get("candidate_name", "unknown")
            email = structured_data.get("email", "")
            hash_input = f"{name}_{email}_{filename}".encode()
            hash_suffix = hashlib.md5(hash_input).hexdigest()[:8].upper()
            structured_data["candidate_id"] = f"CAND_{hash_suffix}"
        
        # Transform skills structure if needed
        if structured_data.get("skills"):
            # If skills is a dict (LLM returned single object), wrap it in a list
            if isinstance(structured_data["skills"], dict):
                structured_data["skills"] = [structured_data["skills"]]
            
            # Sanitize skills: convert None values to empty lists
            skill_categories = [
                "programming_languages", "frameworks", "technologies",
                "technical_skills", "database", "web_technologies",
                "tools", "operating_systems", "soft_skills"
            ]
            for skill_group in structured_data["skills"]:
                if isinstance(skill_group, dict):
                    for category in skill_categories:
                        if category in skill_group and skill_group[category] is None:
                            skill_group[category] = []
            
            # Flatten all skills for all_skills field
            all_skills = []
            for skill_group in structured_data["skills"]:
                if isinstance(skill_group, dict):
                    for category, skills_list in skill_group.items():
                        if isinstance(skills_list, list):
                            all_skills.extend(skills_list)
            structured_data["all_skills"] = list(set(all_skills))  # Remove duplicates
            structured_data["num_skills"] = len(structured_data["all_skills"])
        else:
            # Provide defaults if skills missing
            structured_data["skills"] = []
            structured_data["all_skills"] = []
            structured_data["num_skills"] = 0
        
        # Set num_projects
        if not structured_data.get("num_projects"):
            if structured_data.get("projects_and_technologies_involved"):
                structured_data["num_projects"] = len(structured_data["projects_and_technologies_involved"])
            else:
                structured_data["num_projects"] = 0
        
        # Sanitize projects: convert None values to empty lists for technologies_used
        if structured_data.get("projects_and_technologies_involved"):
            for project in structured_data["projects_and_technologies_involved"]:
                if isinstance(project, dict) and "technologies_used" in project:
                    if project["technologies_used"] is None:
                        project["technologies_used"] = []
        
        # Sanitize work experiences: convert None values to empty lists for used_skills
        if structured_data.get("work_experiences"):
            for work_exp in structured_data["work_experiences"]:
                if isinstance(work_exp, dict) and "used_skills" in work_exp:
                    if work_exp["used_skills"] is None:
                        work_exp["used_skills"] = []
        
        # Ensure default values for list fields
        if not structured_data.get("projects_and_technologies_involved"):
            structured_data["projects_and_technologies_involved"] = []
        if not structured_data.get("certificates_or_qualifications"):
            structured_data["certificates_or_qualifications"] = []
        if not structured_data.get("work_experiences"):
            structured_data["work_experiences"] = []
        
        # Validate with Pydantic model
        try:
            extracted_data = ExtractedData(**structured_data)
            logger.info(f"✓ Validation successful: {extracted_data.num_skills} skills, {extracted_data.num_projects} projects")
            return extracted_data
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            logger.debug(f"Structured data: {json.dumps(structured_data, indent=2)}")
            raise ValueError(f"Failed to validate extracted data: {e}")


# Singleton instance
_cv_parser_service = None

def get_cv_parser_service() -> CVParserService:
    """Get or create singleton CVParserService instance."""
    global _cv_parser_service
    if _cv_parser_service is None:
        _cv_parser_service = CVParserService()
    return _cv_parser_service
