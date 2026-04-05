"""
Job Gap Analysis Router - FastAPI endpoints for JD-based gap analysis.

Provides:
- POST /job-gap/analyze - Upload JD image/PDF and get gap analysis
- GET /job-gap/{job_id} - Get stored job posting details
- DELETE /job-gap/{job_id} - Delete job posting from KG

Example curl:
    curl -X POST "http://localhost:8003/job-gap/analyze" \
         -H "Content-Type: multipart/form-data" \
         -F "candidate_id=cand_001" \
         -F "jd_file=@job_description.png" \
         -F "store_job=true" \
         -F "top_k=25"
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query
from pydantic import BaseModel, Field
from typing import List

from database import Neo4jConnection
from services import get_job_gap_service
from models.schemas import ExtractedData
from agents.kg_writer import KGWriterTool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-gap", tags=["Job Gap Analysis"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SkillGapItem(BaseModel):
    """Skill gap item in response."""
    skill: str = Field(..., description="Skill name")
    importance: float = Field(..., ge=0, le=1, description="Skill importance for role")
    match_strength: float = Field(..., ge=0, le=1, description="How well candidate matches")
    deficit: float = Field(..., ge=0, description="Skill gap (importance × (1 - match))")


class JobGapResponse(BaseModel):
    """Response from job gap analysis."""
    job_id: str = Field(..., description="Unique job posting ID")
    candidate_id: str = Field(..., description="Candidate identifier")
    job_title: str = Field(..., description="Extracted job title")
    readiness: float = Field(..., ge=0, le=1, description="Overall readiness score (1 - skill_gap_index)")
    skill_gap_index: float = Field(..., ge=0, le=1, description="Gap index = sum(deficit)/sum(importance)")
    matched_skills: List[SkillGapItem] = Field(default=[], description="Skills candidate has")
    missing_skills_ranked: List[SkillGapItem] = Field(default=[], description="Missing skills by deficit")
    explanation_text: str = Field(..., description="Plain English explanation")
    candidate_upsert: Optional[dict] = Field(None, description="Candidate KG write result")
    error: Optional[str] = Field(None, description="Error message if any")


class JobPostingInfo(BaseModel):
    """Stored job posting information."""
    job_id: str
    title: str
    source: str
    created_at: str
    skill_count: int
    skills: List[dict]


# ============================================================================
# EXAMPLE CANDIDATE JSON
# ============================================================================

EXAMPLE_CANDIDATE_JSON = """{
  "candidate_id": "cand_ml_001",
  "candidate_name": "Sarah Chen",
  "email": "sarah.chen@email.com",
  "mobile_number": "+94 77 123 4567",
  "current_role": "ML Engineer",
  "target_role": "Senior ML Engineer",
  "current_employment": "AI Solutions Ltd",
  "education": {
    "degree": "BSc Computer Science",
    "university": "University of Colombo"
  },
  "skills": [{
    "programming_languages": ["Python", "Java", "R"],
    "frameworks": ["TensorFlow", "PyTorch", "FastAPI"],
    "technologies": ["Docker", "AWS", "Kubernetes"],
    "technical_skills": ["Machine Learning", "Deep Learning", "NLP"],
    "database": ["PostgreSQL", "MongoDB"],
    "soft_skills": ["Communication", "Leadership"]
  }],
  "projects_and_technologies_involved": [
    {
      "project_name": "Sentiment Analysis Pipeline",
      "project_description": "Built NLP pipeline for customer sentiment analysis",
      "duration": "Jan 2024 – Mar 2024",
      "complexity": "High",
      "technologies_used": ["Python", "TensorFlow", "Docker"]
    }
  ],
  "certificates_or_qualifications": [
    "AWS Certified ML Specialty",
    "TensorFlow Developer Certificate"
  ],
  "all_skills": ["Python", "Java", "R", "TensorFlow", "PyTorch", "FastAPI", "Docker", "AWS", "Kubernetes", "Machine Learning", "Deep Learning", "NLP", "PostgreSQL", "MongoDB"],
  "num_skills": 14,
  "experience_months": 36,
  "experience_level": "Mid-Level",
  "num_projects": 1
}"""


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/analyze",
    response_model=JobGapResponse,
    summary="Analyze gap between candidate and job description",
    description="""
Upload a job description image/PDF along with candidate JSON data to analyze the skill gap.

**Input:**
- `candidate_json`: JSON string containing candidate profile (ExtractedData format)
- `jd_file`: Job description image (PNG, JPG) or PDF
- `store_job`: Whether to store JobPosting in Neo4j (default: true)
- `top_k`: Number of top skills to analyze (default: 25)

**Pipeline:**
1. Parse `candidate_json` into candidate profile
2. Upsert candidate into Neo4j (Person, Skills, Projects, Education, Certifications)
3. OCR extraction from JD using Chandra (HuggingFace)
4. Skill extraction from JD text
5. Skill normalization via embedding shortlist + HuggingFace LLM
6. Build JobPosting skill profile with importance weights
7. Store JobPosting to Neo4j if `store_job=true`
8. Compute candidate-vs-job gap:
   - `deficit = importance × (1 - match_strength)`
   - `skill_gap_index = sum(deficit) / sum(importance)`
   - `readiness = 1 - skill_gap_index`
9. Generate plain English explanation

**Supported file types:**
- Images: PNG, JPG, JPEG
- Documents: PDF

**Note:** First-time processing may be slower due to HuggingFace model loading.
"""
)
async def analyze_job_gap(
    candidate_json: str = Form(
        ...,
        description="Candidate JSON data (ExtractedData format - see Swagger schema)",
        example=EXAMPLE_CANDIDATE_JSON
    ),
    jd_file: UploadFile = File(
        ...,
        description="Job description image (PNG, JPG) or PDF file"
    ),
    store_job: bool = Form(
        True,
        description="Whether to store JobPosting in Knowledge Graph"
    ),
    top_k: int = Form(
        25,
        ge=1,
        le=100,
        description="Number of top skills to analyze"
    )
):
    """
    Analyze skill gap between candidate (from JSON) and uploaded job description.
    
    Returns readiness score, skill_gap_index, matched skills, missing skills ranked by deficit,
    and a plain English explanation.
    """
    logger.info(f"Job gap analysis request: file={jd_file.filename}")
    
    # Step 1: Parse candidate JSON
    try:
        candidate_data = json.loads(candidate_json)
        candidate_id = candidate_data.get("candidate_id")
        
        if not candidate_id:
            raise HTTPException(
                status_code=400,
                detail="candidate_json must contain 'candidate_id' field"
            )
        
        # Validate and convert to ExtractedData model
        extracted_data = ExtractedData(**candidate_data)
        
        logger.info(f"Parsed candidate: {candidate_id}, skills: {len(extracted_data.all_skills or [])}")
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in candidate_json: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid candidate data: {str(e)}"
        )
    
    # Validate file type
    content_type = jd_file.content_type or ""
    valid_types = ["image/", "application/pdf"]
    if not any(t in content_type for t in valid_types):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Use image or PDF."
        )
    
    # Read file content
    file_content = await jd_file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Step 2: Upsert candidate into Neo4j
    candidate_upsert_result = None
    try:
        with Neo4jConnection.get_session() as session:
            kg_result = KGWriterTool.write_candidate(session, extracted_data)
            candidate_upsert_result = {
                "success": kg_result.success,
                "nodes_created": kg_result.nodes_created,
                "relationships_created": kg_result.relationships_created,
                "message": kg_result.message
            }
            logger.info(f"Candidate {candidate_id} upserted: {kg_result.nodes_created} nodes, {kg_result.relationships_created} rels")
    except Exception as e:
        logger.error(f"Failed to upsert candidate: {e}")
        candidate_upsert_result = {"success": False, "error": str(e)}
    
    # Step 3-9: Run gap analysis pipeline
    try:
        with Neo4jConnection.get_session() as session:
            service = get_job_gap_service(session)
            
            result = await service.analyze_job_gap(
                candidate_id=candidate_id,
                file_content=file_content,
                content_type=content_type,
                store_job=store_job,
                top_k=top_k
            )
        
        # Map to response model
        return JobGapResponse(
            job_id=result["job_id"],
            candidate_id=candidate_id,
            job_title=result["job_title"],
            readiness=result["readiness"],
            skill_gap_index=result["skill_gap_index"],
            matched_skills=[
                SkillGapItem(**s) for s in result["matched_skills"]
            ],
            missing_skills_ranked=[
                SkillGapItem(**s) for s in result["missing_skills_ranked"]
            ],
            explanation_text=result["explanation_text"],
            candidate_upsert=candidate_upsert_result,
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Job gap analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/extract",
    summary="Extract and normalize skills from JD",
    description="Upload a job description and see the extraction and normalization output without gap analysis."
)
async def extract_and_normalize(
    jd_file: UploadFile = File(..., description="Job description image/PDF file")
):
    """
    Extract and normalize skills from a job description file.
    
    Returns the OCR text, extracted skills, and normalized skills without performing gap analysis.
    Useful for debugging and verifying the extraction pipeline.
    
    Example:
        curl -X POST "http://localhost:8003/job-gap/extract" \\
             -F "jd_file=@job_description.png"
    """
    try:
        # Step 1: Read file content
        file_content = await jd_file.read()
        content_type = jd_file.content_type or "application/octet-stream"
        
        logger.info(f"Processing JD file: {jd_file.filename} ({len(file_content)} bytes)")
        
        # Step 2: OCR - Extract text from image/PDF
        with Neo4jConnection.get_session() as session:
            service = get_job_gap_service(session)
            
            # Use the OCR service directly
            from services.chandra_ocr_service import get_ocr_service
            ocr_service = get_ocr_service()
            
            ocr_text, ocr_metadata = await ocr_service.process_upload(file_content, content_type)
            
            if not ocr_text or not ocr_text.strip():
                return {
                    "success": False,
                    "error": "OCR extraction failed - no text extracted from file",
                    "ocr_text": "",
                    "ocr_metadata": ocr_metadata,
                    "extracted_skills": {},
                    "normalized_skills": []
                }
            
            logger.info(f"OCR extracted {len(ocr_text)} characters from {ocr_metadata.get('source', 'unknown')}")
            
            # Step 3: Extract skills from OCR text
            from services.skill_extract_service import SkillExtractService
            extract_service = SkillExtractService()
            
            extraction_result = extract_service.extract_skills(ocr_text)
            
            # Get required and optional skills
            raw_required = extraction_result.get("raw_required_skills", [])
            raw_optional = extraction_result.get("raw_optional_skills", [])
            all_extracted = raw_required + raw_optional
            
            job_title = extraction_result.get("job_title", "Unknown")
            
            logger.info(f"Extracted {len(raw_required)} required, {len(raw_optional)} optional skills")
            
            # Step 4: Normalize skills
            from services.skill_normalize_llm import SkillNormalizeLLMService
            normalize_service = SkillNormalizeLLMService()
            
            # Normalize all extracted skills
            normalized_results = normalize_service.normalize_skills_batch(all_extracted)
            
            # Get just the normalized skill names (matched skills only)
            normalized_skills = [r["normalized_skill"] for r in normalized_results if r.get("matched", False)]
            
            logger.info(f"Normalized {len(all_extracted)} skills to {len(normalized_skills)} unique skills")
            
            # Return comprehensive output
            return {
                "success": True,
                "filename": jd_file.filename,
                "job_title": job_title,
                "ocr_text": ocr_text,
                "ocr_text_length": len(ocr_text),
                "ocr_metadata": ocr_metadata,
                "extracted_skills": {
                    "required": raw_required,
                    "optional": raw_optional,
                    "total_count": len(all_extracted)
                },
                "normalization_results": normalized_results,
                "normalized_skills": normalized_skills,
                "normalized_skills_count": len(normalized_skills),
                "skill_mapping": {
                    all_extracted[i]: normalized_results[i]
                    for i in range(len(all_extracted))
                }
            }
    
    except Exception as e:
        logger.error(f"Extraction and normalization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get(
    "/{job_id}",
    response_model=JobPostingInfo,
    summary="Get stored job posting",
    description="Retrieve details of a previously stored job posting."
)
def get_job_posting(job_id: str):
    """Get job posting details from Knowledge Graph."""
    logger.info(f"Getting job posting: {job_id}")
    
    with Neo4jConnection.get_session() as session:
        query = """
        MATCH (j:JobPosting {job_id: $job_id})
        OPTIONAL MATCH (j)-[r:REQUIRES_SKILL]->(s:Skill)
        WITH j, collect({skill: s.name, importance: r.importance}) AS skills
        RETURN j.job_id AS job_id,
               j.title AS title,
               j.source AS source,
               toString(j.created_at) AS created_at,
               size(skills) AS skill_count,
               skills
        """
        
        result = session.run(query, job_id=job_id)
        record = result.single()
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Job posting not found: {job_id}")
        
        return JobPostingInfo(
            job_id=record["job_id"],
            title=record["title"] or "",
            source=record["source"] or "",
            created_at=record["created_at"] or "",
            skill_count=record["skill_count"],
            skills=record["skills"]
        )


@router.delete(
    "/{job_id}",
    summary="Delete job posting",
    description="Remove a job posting and its skill edges from Knowledge Graph."
)
def delete_job_posting(job_id: str):
    """Delete job posting from Knowledge Graph."""
    logger.info(f"Deleting job posting: {job_id}")
    
    with Neo4jConnection.get_session() as session:
        # Check exists
        check = session.run(
            "MATCH (j:JobPosting {job_id: $job_id}) RETURN j LIMIT 1",
            job_id=job_id
        )
        if not check.single():
            raise HTTPException(status_code=404, detail=f"Job posting not found: {job_id}")
        
        # Delete with relationships
        session.run(
            "MATCH (j:JobPosting {job_id: $job_id}) DETACH DELETE j",
            job_id=job_id
        )
    
    return {"message": f"Job posting {job_id} deleted", "job_id": job_id}


@router.get(
    "/",
    summary="List job postings",
    description="List all stored job postings."
)
def list_job_postings(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
):
    """List all job postings in Knowledge Graph."""
    logger.info(f"Listing job postings: limit={limit}, skip={skip}")
    
    with Neo4jConnection.get_session() as session:
        query = """
        MATCH (j:JobPosting)
        OPTIONAL MATCH (j)-[:REQUIRES_SKILL]->(s:Skill)
        WITH j, count(s) AS skill_count
        RETURN j.job_id AS job_id,
               j.title AS title,
               j.source AS source,
               toString(j.created_at) AS created_at,
               skill_count
        ORDER BY j.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        result = session.run(query, skip=skip, limit=limit)
        
        jobs = [
            {
                "job_id": r["job_id"],
                "title": r["title"],
                "source": r["source"],
                "created_at": r["created_at"],
                "skill_count": r["skill_count"]
            }
            for r in result
        ]
    
    return {"jobs": jobs, "count": len(jobs)}
