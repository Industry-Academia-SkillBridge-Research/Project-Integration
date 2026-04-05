import os
import sys
import json
import logging
from typing import List, Optional, Union
from datetime import datetime
from dotenv import load_dotenv
import requests as http_requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
import google.genai as genai
import ollama

from neo4j import GraphDatabase

from feedback.storage import log_model_output, get_current_prompt_version
from feedback.schemas import FeedbackEntry
from feedback import storage as feedback_storage

import threading

def _trigger_seed_extraction():
    """Re-extract real seeds from the model output log in a background thread."""
    try:
        import importlib.util, os as _os
        spec = importlib.util.spec_from_file_location(
            "extract_real_seeds",
            _os.path.join(_os.path.dirname(__file__), "datasets", "extract_real_seeds.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.extract_seeds()
    except Exception as exc:
        logger.warning(f"[seed extraction] Failed: {exc}")

# Import service clients
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'clients'))
from clients import AgentRuntimeClient, RecommendationClient



# --- CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Externalized Model Config
DEFAULT_OLLAMA_FINE_TUNED = os.getenv("OLLAMA_MODEL_FINETUNED", "my-gemma3:latest")
DEFAULT_OLLAMA_GENERIC = os.getenv("OLLAMA_MODEL_GENERIC", "gemma3:1b")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# External service URLs (set in .env or use defaults)
LINKEDIN_SCRAPER_URL = os.getenv("LINKEDIN_SCRAPER_URL", "http://localhost:8000")
AGENT_RUNTIME_URL   = os.getenv("AGENT_RUNTIME_URL",   "http://localhost:8003")
ROLE_SKILL_API_URL  = os.getenv("ROLE_SKILL_API_URL",  "http://localhost:8181")

# Neo4j Configuration (for reading scraped job data directly)
NEO4J_URI      = os.getenv("NEO4J_URI",      "neo4j+s://2185b358.databases.neo4j.io")
NEO4J_USER     = os.getenv("NEO4J_USER",     "2185b358")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "X3Ch4_CveKUANRq13aOyQcE29DpyanwIVlirgwo0OyI")

_neo4j_driver = None

def _get_neo4j_driver():
    """Lazy-init a shared Neo4j driver (reused across requests)."""
    global _neo4j_driver
    if _neo4j_driver is None:
        try:
            _neo4j_driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            _neo4j_driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    return _neo4j_driver


def _neo4j_query(cypher: str, parameters: dict = None) -> list[dict]:
    """Run a read query against Neo4j and return list of record dicts."""
    driver = _get_neo4j_driver()
    with driver.session() as session:
        result = session.run(cypher, parameters or {})
        return [record.data() for record in result]

app = FastAPI(title="Skill Gap & Project Generator API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DOMAIN MODELS ---
class StudentData(BaseModel):
    name: str
    current_role: str
    skills: List[str]
    experience_summary: str
    # Added to match fine-tuning dataset
    major: Optional[str] = "Undeclared"
    interests: Optional[List[str]] = []
    personality: Optional[str] = "ambitious, learner"

class JobData(BaseModel):
    role: str
    required_skills: List[str]
    description_summary: str

class ProjectRequest(BaseModel):
    student_data: StudentData
    job_data: JobData
    target_role: str
    model_provider: str = "gemini"  # "gemini", "ollama", "ollama_generic"
    ollama_model: Union[str, None] = None


# --- COMBINED SOURCE REQUEST ---
# Mirrors the Agent-Runtime `extracted_data` format so callers can pass
# a candidate profile directly (as returned by the LPR Agent-Runtime API)
# without needing a separate lookup round-trip.

class WorkExperience(BaseModel):
    title: str
    company_name: Optional[str] = ""
    duration_months: Optional[int] = 0
    skills_used: Optional[List[str]] = []

class CandidateSkill(BaseModel):
    skill_name: str
    proficiency: Optional[str] = "intermediate"

class CandidateProject(BaseModel):
    name: str
    description: Optional[str] = ""
    technologies: Optional[List[str]] = []

class CandidateProfile(BaseModel):
    """Mirrors Agent-Runtime extracted_data schema."""
    candidate_id: str
    name: str
    current_role: Optional[str] = "Student"
    experience_level: Optional[str] = "entry"
    total_experience_months: Optional[int] = 0
    skills: Optional[List[CandidateSkill]] = []
    work_experiences: Optional[List[WorkExperience]] = []
    projects: Optional[List[CandidateProject]] = []
    field_of_study: Optional[str] = "Undeclared"
    interests: Optional[List[str]] = []
    personality: Optional[str] = "ambitious, learner"

class CombinedSourceRequest(BaseModel):
    """
    Request that lets the caller supply identifiers for external services
    instead of filling StudentData/JobData manually.

    Priority rules
    --------------
    - job_id          → fetch JobResponse from LinkedIn Scraper API
    - candidate_id    → fetch CandidateProfile from Agent-Runtime API
    - role_key        → optionally enrich required_skills from Role-Skill-API
    - inline_*        → use directly (skips external fetch)
    """
    # Job source – one of: job_id OR inline_job
    job_id:         Optional[str] = None
    inline_job:     Optional[JobData] = None

    # Candidate source – one of: candidate_id OR inline_candidate
    candidate_id:       Optional[str] = None
    inline_candidate:   Optional[CandidateProfile] = None

    # Optional: enrich job skills from Role-Skill-API
    role_key:       Optional[str] = None

    # Generation settings
    model_provider: str = "gemini"
    ollama_model:   Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "data-engineer-techcorp-123456",
                "candidate_id": "CAND_ML_2024_001",
                "role_key": "data_engineer",
                "model_provider": "gemini"
            }
        }
    )

# --- PROMPTS ---
SYSTEM_PROMPT = """
You are an expert Technical Career Coach and Solutions Architect.
Your goal is to identify skill gaps and recommend a high-impact capstone project.

Output must be valid JSON with this structure:
{
    "gap_analysis": {
        "missing_skills": ["List", "of", "skills"],
        "match_percentage": <0-100>,
        "analysis_summary": "Concise gap explanation."
    },
    "project_recommendation": {
        "project_title": "Impressive Project Name",
        "objective": "Primary learning goal.",
        "tech_stack": ["Tech1", "Tech2"],
        "implementation_steps": ["Step 1", "Step 2"]
    }
}
"""

# --- HELPER FUNCTIONS ---

# ── External service fetchers ──────────────────────────────────────────────

def fetch_linkedin_job(job_id: str) -> dict:
    """
    Fetch a single job from Neo4j by job_id.
    Falls back to the LinkedIn Scraper API if Neo4j is unavailable.
    """
    # Primary: query Neo4j directly
    try:
        rows = _neo4j_query(
            """
            MATCH (j:Job {job_id: $job_id})
            OPTIONAL MATCH (r:Role {role_key: j.role_key})
            RETURN j { .*, role_name: r.name } AS job
            """,
            {"job_id": job_id},
        )
        if rows and rows[0].get("job"):
            return rows[0]["job"]
    except Exception as e:
        logger.warning(f"Neo4j lookup failed for job_id={job_id}: {e}")

    # Fallback: scraper API (if Docker containers are running)
    url = f"{LINKEDIN_SCRAPER_URL}/api/v1/job/{job_id}"
    try:
        resp = http_requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Job not found in Neo4j or Scraper API for job_id='{job_id}': {e}"
        )


def fetch_candidate_profile(candidate_id: str) -> dict:
    """
    Fetch a candidate profile from the Agent-Runtime API.
    Endpoint: GET /candidates/{candidate_id}
    """
    url = f"{AGENT_RUNTIME_URL}/candidates/{candidate_id}"
    try:
        resp = http_requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Agent-Runtime API error for candidate_id='{candidate_id}': {e}"
        )


def fetch_role_skills(role_key: str, top_n: int = 15) -> List[str]:
    """
    Fetch top required skills for a role from the Role-Skill-API.
    Endpoint: GET /roles/{role_key}/skills?top_n=N
    Returns a plain list of skill names.
    """
    url = f"{ROLE_SKILL_API_URL}/roles/{role_key}/skills"
    try:
        resp = http_requests.get(url, params={"top_n": top_n}, timeout=10)
        resp.raise_for_status()
        profile = resp.json()           # RoleSkillProfile
        return [s["name"] for s in profile.get("skills", [])]
    except Exception as e:
        logger.warning(f"Role-Skill-API unavailable for role_key='{role_key}': {e}")
        return []  # non-fatal – caller merges with existing skills


# ── Data mappers ───────────────────────────────────────────────────────────

def linkedin_job_to_job_data(job: dict) -> tuple[JobData, str]:
    """
    Map a LinkedIn Scraper `JobResponse` dict → (JobData, target_role).

    LinkedIn field        → Recommendation field
    --------------------------------------------------
    title                 → role  +  target_role
    skills                → required_skills
    description (≤500ch)  → description_summary
    """
    title       = job.get("title", "Unknown Role")
    skills      = job.get("skills") or []
    description = (job.get("description") or "")[:500]

    return (
        JobData(
            role=title,
            required_skills=skills,
            description_summary=description or f"Targeting a role as {title}",
        ),
        title,  # used as target_role
    )


def candidate_profile_to_student_data(profile: dict) -> StudentData:
    """
    Map an Agent-Runtime `extracted_data` / CandidateProfile dict
    → StudentData for the recommendation API.

    Agent-Runtime field               → Recommendation field
    ----------------------------------------------------------
    name                              → name
    current_role (or experiences[0]) → current_role
    skills[*].skill_name             → skills
    work_experiences (formatted)     → experience_summary
    field_of_study                   → major
    interests                        → interests
    personality                      → personality
    """
    name            = profile.get("name") or profile.get("candidate_name", "Candidate")
    experiences     = profile.get("work_experiences") or []
    current_role    = (
        profile.get("current_role")
        or (experiences[0]["title"] if experiences else "Student")
    )

    # Flatten skill objects → plain names
    raw_skills = profile.get("skills") or []
    skills = [
        s["skill_name"] if isinstance(s, dict) else str(s)
        for s in raw_skills
    ]

    # Build experience summary from work history + projects
    exp_parts = [
        f"{e.get('title','Role')} at {e.get('company_name','?')} "
        f"({e.get('duration_months', 0)} months)"
        for e in experiences
    ]
    projects    = profile.get("projects") or []
    proj_parts  = [
        f"Project: {p.get('name','')} – {(p.get('description') or '')[:120]}"
        for p in projects[:3]
    ]
    experience_summary = ". ".join(exp_parts + proj_parts) or "No prior experience recorded."

    return StudentData(
        name=name,
        current_role=current_role,
        skills=skills,
        experience_summary=experience_summary,
        major=profile.get("field_of_study", "Undeclared"),
        interests=profile.get("interests") or [
            p.get("name", "") for p in projects[:3]
        ],
        personality=profile.get("personality", "ambitious, learner"),
    )


def construct_analysis_prompt(request: ProjectRequest, system_prompt: str) -> str:
    """
    Constructs a consistent prompt for generic models (Gemini & Generic Ollama).
    """
    return f"""
    Analyze this student against the target job.

    STUDENT PROFILE:
    Name: {request.student_data.name}
    Role: {request.student_data.current_role}
    Major: {request.student_data.major}
    Interests: {', '.join(request.student_data.interests)}
    Personality: {request.student_data.personality}
    Skills: {', '.join(request.student_data.skills)}
    Experience: {request.student_data.experience_summary}

    TARGET JOB:
    Role: {request.job_data.role}
    Required Skills: {', '.join(request.job_data.required_skills)}
    Description: {request.job_data.description_summary}

    {system_prompt}
    """


def _build_input_dict(request: ProjectRequest) -> dict:
    """Build a serializable dict of the request input for logging."""
    return {
        "student_data": {
            "demographics": f"{request.student_data.name}, {request.student_data.current_role}",
            "major": request.student_data.major,
            "interests": request.student_data.interests,
            "current_skills": request.student_data.skills,
            "personality": request.student_data.personality,
        },
        "job_data": {
            "target_job_role": request.target_role,
            "required_skills": request.job_data.required_skills,
            "description": request.job_data.description_summary,
        },
    }


async def logging_wrapper(generator, input_data: dict, provider: str):
    """Wraps async generators to log complete output after streaming finishes."""
    full_text = ""
    async for chunk in generator:
        full_text += chunk
        yield chunk
    # Stream complete - log the output for feedback collection
    try:
        prompt_version = get_current_prompt_version()
        log_model_output(input_data, full_text, provider, prompt_version)
        # Re-extract real seeds so the dataset stays current after each generation
        threading.Thread(target=_trigger_seed_extraction, daemon=True).start()
    except Exception as e:
        logger.warning(f"Failed to log model output: {e}")

# --- LOGIC HANDLERS ---

async def run_gemini(request: ProjectRequest):
    """
    Executes logic using Google's Gemini Flash model (Latest).
    Yields raw text chunks for streaming.
    """
    try:
        if not gemini_client:
            yield "Error: Gemini API key not configured"
            return

        # Unified Prompt
        user_prompt = construct_analysis_prompt(request, SYSTEM_PROMPT)

        response = gemini_client.models.generate_content_stream(
            model=GEMINI_MODEL_ID,
            contents=user_prompt,
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        yield f"Error: {str(e)}"


async def run_ollama(request: ProjectRequest):
    """
    Executes logic using Ollama (Fine-tuned or Generic).
    Yields raw text chunks for streaming.
    """
    try:
        # Determine model to use
        if request.model_provider == "ollama_generic":
             model_id = request.ollama_model or DEFAULT_OLLAMA_GENERIC
        else:
             # Default to fine-tuned
             model_id = request.ollama_model or DEFAULT_OLLAMA_FINE_TUNED

        is_finetuned_logic = (model_id == DEFAULT_OLLAMA_FINE_TUNED)
        
        # Prepare Prompt based on Model Type
        if is_finetuned_logic:
            # Fine-tuned models expect specific compact input structure matching training data
            input_json = {
                "student_data": {
                    "demographics": f"{request.student_data.name}, {request.student_data.current_role}",
                    "major": request.student_data.major,
                    "interests": request.student_data.interests,
                    "current_skills": request.student_data.skills,
                    "personality": request.student_data.personality
                },
                "job_data": {
                    "target_job_role": request.target_role,
                    "required_skills": request.job_data.required_skills,
                    "description": request.job_data.description_summary
                }
            }
            prompt = json.dumps(input_json)
        else:
            # Generic models now use the SAME prompt logic as Gemini
            prompt = construct_analysis_prompt(request, SYSTEM_PROMPT)

        # Stream from Ollama
        stream = ollama.chat(
            model=model_id,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True,
            options={"temperature": 1.0} 
        )

        for chunk in stream:
            content = chunk['message']['content']
            yield content

    except Exception as e:
        logger.error(f"Ollama Error: {e}")
        yield f"Error: {str(e)}"


# --- API ENDPOINTS ---

@app.post("/generate-project")
async def generate_project(request: ProjectRequest):
    """
    Unified endpoint for project generation.
    Stream raw text to allow frontend parsing/display.
    Logs the complete output for feedback collection.
    """
    input_data = _build_input_dict(request)

    if request.model_provider == "gemini":
        generator = run_gemini(request)
    else:
        # Covers "ollama" and "ollama_generic"
        generator = run_ollama(request)

    # Wrap with logging to capture output for feedback
    logged_generator = logging_wrapper(generator, input_data, request.model_provider)
    return StreamingResponse(logged_generator, media_type="text/plain")


@app.post("/generate-project-from-sources")
async def generate_project_from_sources(req: CombinedSourceRequest):
    """
    Updated endpoint that orchestrates Agent-Runtime and Advanced-Recommendation.
    
    Now returns comprehensive analysis including:
    - Skill gaps from Advanced-Recommendation
    - Course recommendations
    - Project relevance analysis
    - GNN-based missing skills
    
    Data resolution order:
    Job data:
      1. ``job_id``       → fetched from Neo4j (if available)
      2. ``inline_job``   → used directly
    
    Candidate data:
      1. ``candidate_id`` → fetched from Agent-Runtime API
      2. ``inline_candidate`` → used directly
    
    Optional:
      ``role_key`` → enriches skills from Advanced-Recommendation
    """
    logger.info(f"Combined source request: candidate={req.candidate_id}, job={req.job_id}, role={req.role_key}")
    
    try:
        # Initialize clients
        agent_client = AgentRuntimeClient()
        rec_client = RecommendationClient()
        
        # ── 1. Resolve candidate data ──────────────────────────────────────
        candidate_id = None
        cv_analysis = None
        
        if req.candidate_id:
            logger.info(f"Fetching CV analysis from Agent-Runtime for {req.candidate_id}...")
            try:
                cv_analysis = agent_client.skill_explain(
                    candidate_id=req.candidate_id,
                    role_key=req.role_key or "ai_ml_engineer",
                    top_n=10
                )
                candidate_id = req.candidate_id
                logger.info(f"✓ CV analysis retrieved")
            except Exception as e:
                logger.warning(f"Failed to get CV analysis: {e}")
        
        if not candidate_id and not req.inline_candidate:
            raise HTTPException(
                status_code=422,
                detail="Provide either 'candidate_id' or 'inline_candidate'."
            )
        
        if req.inline_candidate:
            candidate_id = req.inline_candidate.candidate_id
        
        # ── 2. Resolve role/job data ──────────────────────────────────────
        role_key = req.role_key or "ai_ml_engineer"
        
        # ── 3. Fetch comprehensive analysis ───────────────────────────────
        logger.info(f"Fetching comprehensive analysis for {candidate_id} → {role_key}...")
        
        results = {
            "candidate_id": candidate_id,
            "role_key": role_key,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Get skill gaps
        try:
            gap_response = rec_client.skill_gap(candidate_id, role_key, top_k=25)
            results["skill_gap"] = gap_response
            logger.info(f"✓ Skill gaps: {len(gap_response.get('deficits', []))} deficits")
        except Exception as e:
            logger.warning(f"Skill gap fetch failed: {e}")
            results["skill_gap_error"] = str(e)
        
        # Get course recommendations
        try:
            courses_response = rec_client.recommend_courses(candidate_id, role_key, top_k=25, top_n=10)
            results["recommendations"] = courses_response
            logger.info(f"✓ Course recommendations: {len(courses_response.get('recommendations', []))} courses")
        except Exception as e:
            logger.warning(f"Course recommendation failed: {e}")
            results["recommendations_error"] = str(e)
        
        # Get project relevance
        try:
            projects_response = rec_client.project_relevance(candidate_id, role_key, top_n=5)
            results["project_relevance"] = projects_response
            logger.info(f"✓ Project relevance: score={projects_response.get('candidate_project_score')}")
        except Exception as e:
            logger.warning(f"Project relevance failed: {e}")
            results["project_relevance_error"] = str(e)
        
        # Get GNN missing skills (optional)
        try:
            gnn_response = rec_client.missing_skills_gnn(candidate_id, role_key, top_k=15)
            if gnn_response.get("gnn_available"):
                results["missing_skills_gnn"] = gnn_response
                logger.info(f"✓ GNN analysis: {len(gnn_response.get('missing_skills', []))} skills")
        except Exception as e:
            logger.info(f"⚠ GNN analysis unavailable (non-critical): {e}")
        
        # ── 4. Return comprehensive results ────────────────────────────────
        logger.info(f"✓ Analysis complete for {candidate_id}")
        return JSONResponse(status_code=200, content=results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Combined source request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/roles")
async def list_roles():
    """
    Fetch available roles from Advanced-Recommendation service.
    Used by frontend to populate role dropdowns.
    """
    try:
        rec_client = RecommendationClient()
        roles = rec_client.list_roles()
        return {
            "roles": roles,
            "count": len(roles),
        }
    except Exception as e:
        logger.error(f"Failed to fetch roles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch roles: {str(e)}"
        )


@app.post("/submit-feedback")
async def submit_feedback(entry: FeedbackEntry):
    """Accept expert feedback on a model output."""
    try:
        feedback_storage.save_feedback(entry)
        return {"status": "ok", "feedback_id": entry.feedback_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unreviewed-outputs")
async def get_unreviewed():
    """Return model outputs that have not been reviewed by experts."""
    return feedback_storage.load_unreviewed_outputs()


@app.get("/feedback-status")
async def get_feedback_status():
    """Return current feedback collection status."""
    from feedback.pipeline import get_evolution_status
    return get_evolution_status()


# --- NEW ENDPOINTS FOR REACT FRONTEND ---

@app.get("/all-feedback")
async def get_all_feedback():
    """Load all feedback entries."""
    entries = feedback_storage.load_all_feedback()
    return [e.model_dump() for e in entries]


@app.get("/my-outputs")
async def get_my_outputs(student_name: str):
    """
    Return all model outputs for a specific student, together with any
    expert feedback that was given on each output.

    Matching strategy: the ``model_input.student_data.demographics`` field
    stores ``"{name}, {role}"`` – we accept a match if the demographics string
    starts with the requested name (case-insensitive).
    """
    name_lower = student_name.strip().lower()

    # ── 1. Collect all outputs belonging to this student ──────────────────
    all_outputs = feedback_storage.load_all_outputs()
    student_outputs = []
    for out in all_outputs:
        demographics = (
            out.get("model_input", {})
               .get("student_data", {})
               .get("demographics", "")
        )
        if demographics.lower().startswith(name_lower):
            student_outputs.append(out)

    # ── 2. Build a lookup: model_output text → feedback entry ─────────────
    all_feedback_entries = feedback_storage.load_all_feedback()
    feedback_by_output: dict = {}
    for fb in all_feedback_entries:
        key = fb.model_output
        # Keep only the first match per output text (there should only be one)
        if key not in feedback_by_output:
            feedback_by_output[key] = fb.model_dump()

    # ── 3. Merge and return ───────────────────────────────────────────────
    results = []
    for out in student_outputs:
        feedback = feedback_by_output.get(out.get("model_output", ""))
        results.append({
            "output": out,
            "feedback": feedback,   # None when no feedback exists yet
        })

    # Most-recent first
    results.sort(key=lambda r: r["output"].get("timestamp", ""), reverse=True)
    return results


class AnalysisRequest(BaseModel):
    provider: str = "ollama"


@app.post("/run-analysis")
async def run_analysis(req: AnalysisRequest):
    """Trigger Phase 1 pattern analysis on collected feedback."""
    from feedback.pipeline import run_analysis_phase
    try:
        report = run_analysis_phase(provider=req.provider)
        return report.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pattern-reports")
async def get_pattern_reports():
    """List all pattern analysis reports."""
    reports = feedback_storage.load_pattern_reports()
    return [r.model_dump() for r in reports]


class EvolutionRequest(BaseModel):
    report_id: str
    provider: str = "ollama"


@app.post("/preview-evolution")
async def preview_evo(req: EvolutionRequest):
    """Preview prompt evolution diff without committing."""
    from feedback.pipeline import run_preview_phase
    try:
        diff = run_preview_phase(req.report_id, provider=req.provider)
        return {"diff": diff}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/apply-evolution")
async def apply_evo(req: EvolutionRequest):
    """Apply prompt evolution permanently."""
    from feedback.pipeline import run_evolution_phase
    try:
        evolution = run_evolution_phase(req.report_id, provider=req.provider)
        return evolution.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/prompt-evolutions")
async def get_evolutions():
    """List all prompt evolution records."""
    evolutions = feedback_storage.load_prompt_evolutions()
    return [e.model_dump() for e in evolutions]


@app.get("/current-prompt")
async def get_current_prompt():
    """Get the current active system prompt and version."""
    from feedback.storage import get_current_system_prompt, get_current_prompt_version
    return {
        "prompt": get_current_system_prompt(),
        "version": get_current_prompt_version(),
    }


class RegenerationRequest(BaseModel):
    evolution_id: str
    provider: str = "ollama"
    target_count: int = 200
    generation_mode: str = "v2"  # "v1" (detailed text) or "v2" (detailed JSON)


@app.post("/run-regeneration")
async def run_regen(req: RegenerationRequest):
    """Start dataset regeneration using an evolved prompt."""
    from feedback.pipeline import run_regeneration_phase
    try:
        output_path = run_regeneration_phase(
            req.evolution_id,
            provider=req.provider,
            target_count=req.target_count,
            generation_mode=req.generation_mode,
        )
        return {"output_path": output_path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/list-datasets")
async def list_datasets():
    """List available generated JSONL dataset files in the datasets/ folder with entry counts."""
    datasets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")
    skip = {"seeds.jsonl", "real_seeds.jsonl", "test_sample.jsonl"}
    result = []
    if os.path.isdir(datasets_dir):
        for fname in sorted(
            f for f in os.listdir(datasets_dir)
            if f.endswith(".jsonl") and f not in skip
        ):
            fpath = os.path.join(datasets_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    count = sum(1 for line in fh if line.strip())
            except Exception:
                count = 0
            result.append({"filename": fname, "entry_count": count})
    return {"datasets": result}


class HFUploadRequest(BaseModel):
    filename: str
    repo_id: Optional[str] = None


@app.post("/upload-to-hf")
async def upload_to_hf(req: HFUploadRequest):
    """Upload a dataset file to HuggingFace Hub."""
    datasets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")
    file_path = os.path.join(datasets_dir, os.path.basename(req.filename))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Dataset file not found: {req.filename}")
    try:
        # Use importlib to avoid conflict with the installed HuggingFace `datasets` package
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            "hf_uploader",
            os.path.join(datasets_dir, "hf_uploader.py"),
        )
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        upload_dataset = _mod.upload_dataset

        success = upload_dataset(
            file_path=file_path,
            commit_message=f"Upload via frontend: {req.filename}",
            repo_id=req.repo_id or None,
        )
        if success:
            return {"status": "success", "filename": req.filename}
        else:
            raise HTTPException(status_code=500, detail="Upload failed. Check HF_TOKEN in .env.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs-by-role")
async def get_jobs_by_role(role_key: Optional[str] = None, limit: int = 100):
    """
    Return scraped jobs grouped by role_key — reads directly from Neo4j.
    Pass ?role_key=ai_ml_engineer to filter to one role.
    Pass no role_key to get all roles with their job lists.
    """
    try:
        if role_key:
            rows = _neo4j_query(
                """
                MATCH (j:Job)
                WHERE j.role_key = $role_key
                RETURN j.job_id        AS job_id,
                       j.title         AS title,
                       j.company_name  AS company,
                       j.location      AS location,
                       j.role_key      AS role_key,
                       j.description   AS description,
                       j.job_url       AS job_url,
                       j.posted_date   AS posted_date
                ORDER BY j.scraped_at DESC
                LIMIT $limit
                """,
                {"role_key": role_key, "limit": limit},
            )
            jobs = [{"job_id": r["job_id"], "title": r["title"],
                     "company": r["company"], "location": r["location"],
                     "role_key": r["role_key"], "description": r.get("description", ""),
                     "job_url": r.get("job_url", ""), "posted_date": r.get("posted_date", "")} for r in rows]
            return {"role_key": role_key, "count": len(jobs), "jobs": jobs}
        else:
            rows = _neo4j_query(
                """
                MATCH (j:Job)
                RETURN j.job_id        AS job_id,
                       j.title         AS title,
                       j.company_name  AS company,
                       j.location      AS location,
                       COALESCE(j.role_key, 'untagged') AS role_key,
                       j.description   AS description,
                       j.job_url       AS job_url,
                       j.posted_date   AS posted_date
                ORDER BY j.scraped_at DESC
                LIMIT $limit
                """,
                {"limit": limit},
            )

            from collections import defaultdict
            grouped: dict = defaultdict(list)
            for r in rows:
                rk = r["role_key"]
                grouped[rk].append({
                    "job_id": r["job_id"], "title": r["title"],
                    "company": r["company"], "location": r["location"],
                    "role_key": rk, "description": r.get("description", ""),
                    "job_url": r.get("job_url", ""), "posted_date": r.get("posted_date", ""),
                })
            return {
                "total": sum(len(v) for v in grouped.values()),
                "role_keys": list(grouped.keys()),
                "by_role": {rk: {"count": len(jobs), "jobs": jobs}
                            for rk, jobs in sorted(grouped.items())},
            }
    except Exception as e:
        logger.error(f"Neo4j query failed in /jobs-by-role: {e}")
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")


@app.get("/search-jobs")
async def search_jobs(
    query: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    Full-text search over Job nodes in Neo4j.
    Replaces the Elasticsearch /api/v1/search endpoint.
    Supports query (title/description), location, and company filters.
    """
    try:
        conditions = []
        params: dict = {"skip": (page - 1) * page_size, "limit": page_size}

        if query:
            # Case-insensitive CONTAINS on title or description
            conditions.append(
                "(toLower(j.title) CONTAINS toLower($query) "
                "OR toLower(j.description) CONTAINS toLower($query))"
            )
            params["query"] = query
        if location:
            conditions.append("toLower(j.location) CONTAINS toLower($location)")
            params["location"] = location
        if company:
            conditions.append("toLower(j.company_name) CONTAINS toLower($company)")
            params["company"] = company

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        cypher = f"""
            MATCH (j:Job)
            {where_clause}
            RETURN j.job_id        AS job_id,
                   j.title         AS title,
                   j.company_name  AS company,
                   j.location      AS location,
                   j.description   AS description,
                   j.job_url       AS job_url,
                   j.posted_date   AS posted_date,
                   COALESCE(j.role_key, 'untagged') AS role_key
            ORDER BY j.scraped_at DESC
            SKIP $skip
            LIMIT $limit
        """
        rows = _neo4j_query(cypher, params)

        # Get total count for pagination
        count_cypher = f"MATCH (j:Job) {where_clause} RETURN count(j) AS total"
        count_rows = _neo4j_query(count_cypher, params)
        total = count_rows[0]["total"] if count_rows else 0

        hits = [{
            "job_id": r["job_id"], "title": r["title"],
            "company": r["company"], "location": r["location"],
            "description": r.get("description", ""),
            "job_url": r.get("job_url", ""),
            "posted_date": r.get("posted_date", ""),
            "role_key": r["role_key"],
        } for r in rows]

        return {
            "total": total,
            "hits": hits,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 1,
        }
    except Exception as e:
        logger.error(f"Neo4j search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Neo4j search error: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
