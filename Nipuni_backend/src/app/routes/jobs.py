"""
Job Recommendation API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import pandas as pd
from ..db import get_db
from ..services.job_recommendation_service import recommend_jobs_for_student
from ..services.ml_job_recommendation_service import recommend_jobs_ml
import logging

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
JOB_DATA_FILE = DATA_DIR / "Job_data.csv"

# Router for student-specific job recommendations
router = APIRouter(prefix="/students", tags=["Job Recommendations"])

# Router for general job endpoints (no prefix)
job_router = APIRouter(tags=["Jobs"])


class SkillMatch(BaseModel):
    skill: str
    score: float


class SkillGap(BaseModel):
    skill: str
    score: float
    gap: float


class JobRecommendation(BaseModel):
    job_id: str
    title: str
    company: str
    role_key: str
    match_score: float = Field(..., description="Overall match score (0-100)")
    total_required_skills: int
    matched_skills_count: int
    missing_skills_count: int
    matched_skills: List[SkillMatch]
    missing_skills: List[SkillGap]
    top_contributors: List[SkillMatch]


@router.get("/{student_id}/jobs/recommend", response_model=List[JobRecommendation], deprecated=True)
def get_job_recommendations_legacy(
    student_id: str,
    top_k: int = Query(default=10, ge=1, le=100, description="Number of jobs to return"),
    threshold: float = Query(default=70.0, ge=0.0, le=100.0, description="Minimum score to consider skill matched"),
    role_key: Optional[str] = Query(default=None, description="Filter by role category (e.g., AIML, FULLSTACK)"),
    db: Session = Depends(get_db)
):
    """
    ⚠️ DEPRECATED: Use `/students/{student_id}/jobs/recommend/ml` instead.
    
    Get personalized job recommendations for a student.
    
    **LEGACY ENDPOINT** - Uses only transcript-claimed skills.
    This endpoint does NOT use validated quiz results from StudentSkillPortfolio.
    
    For ML-enhanced recommendations with verified skills and levels, use:
    GET /students/{student_id}/jobs/recommend/ml
    
    Analyzes student's parent skill scores against job requirements
    and returns ranked recommendations with detailed match analysis.
    
    Args:
        student_id: Student identifier
        top_k: Number of top jobs to return (1-100)
        threshold: Minimum score (0-100) to consider a skill "matched"
        role_key: Optional role filter (AIML, FULLSTACK, DEVOPS, etc.)
        
    Returns:
        List of job recommendations sorted by match score (highest first)
        
    Each recommendation includes:
        - Basic job info (id, title, company, role)
        - Match score: Average of student's scores on required skills
        - Matched skills: Skills where student score >= threshold
        - Missing skills: Skills where student score < threshold (with gap)
        - Top contributors: Student's strongest skills for this job
        
    Example:
        GET /students/IT21013928/jobs/recommend?top_k=5&threshold=75&role_key=AIML
    """
    try:
        recommendations = recommend_jobs_for_student(
            db=db,
            student_id=student_id,
            top_k=top_k,
            threshold=threshold,
            role_key=role_key
        )
        
        if not recommendations:
            logger.warning(
                f"No job recommendations found for student {student_id} "
                f"(role_key={role_key})"
            )
        
        return recommendations
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating job recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate job recommendations: {str(e)}"
        )


@router.get("/{student_id}/jobs/recommend/ml")
def get_ml_job_recommendations(
    student_id: str,
    top_k: int = Query(default=10, ge=1, le=100, description="Number of jobs to return"),
    threshold: float = Query(default=70.0, ge=0.0, le=100.0, description="Minimum score for skill proficiency"),
    use_verified: bool = Query(default=True, description="Prefer verified skills over claimed"),
    role_key: Optional[str] = Query(default=None, description="Filter by role category"),
    db: Session = Depends(get_db)
):
    """
    Get ML-enhanced job recommendations with skill gap analysis.
    
    **NEW ENHANCED ENDPOINT** with Machine Learning:
    - Uses ML model for intelligent job matching
    - Prioritizes verified skills from quiz results
    - Shows skill levels (Beginner/Intermediate/Advanced)
    - Provides detailed skill gap analysis
    - Suggests specific skills to improve
    - Offers actionable next steps
    
    Args:
        student_id: Student identifier
        top_k: Number of recommendations to return (1-100)
        threshold: Minimum score (0-100) for skill proficiency
        use_verified: Use verified skills from quizzes (recommended: True)
        role_key: Optional role filter (AIML, FULLSTACK, DO, etc.)
        
    Returns:
        Enhanced job recommendations with:
        - ML-based match scores
        - Skill proficiency levels
        - Proficient skills (with levels)
        - Skills needing improvement (with recommendations)
        - Missing skills (with learning suggestions)
        - Job readiness assessment
        - Actionable next steps
        
    Example:
        GET /students/IT21013928/jobs/recommend/ml?use_verified=true&threshold=70
    """
    try:
        recommendations = recommend_jobs_ml(
            db=db,
            student_id=student_id,
            top_k=top_k,
            threshold=threshold,
            use_verified=use_verified,
            role_key=role_key
        )
        
        if not recommendations:
            logger.warning(
                f"No ML job recommendations found for student {student_id} "
                f"(role_key={role_key})"
            )
        
        return {
            "student_id": student_id,
            "total_recommendations": len(recommendations),
            "threshold_used": threshold,
            "using_verified_skills": use_verified,
            "ml_enabled": recommendations[0]["ml_prediction"] if recommendations else False,
            "recommendations": recommendations
        }
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"ML job recommendation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate ML job recommendations: {str(e)}"
        )


@job_router.get("/jobs/{job_id}")
def get_job_details(job_id: str):
    """
    Get detailed information for a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Complete job information including description, skills, requirements, etc.
    """
    try:
        # Load job data from CSV
        if not JOB_DATA_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Job data file not found: {JOB_DATA_FILE}"
            )
        
        df = pd.read_csv(JOB_DATA_FILE)
        
        # Find the job
        job_row = df[df['job_id'] == job_id]
        
        if job_row.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}"
            )
        
        # Convert to dict
        job = job_row.iloc[0].to_dict()
        
        # Parse skills list
        skills_str = job.get('skills', '')
        skills_list = [s.strip() for s in skills_str.split('|')] if skills_str else []
        
        # Build response
        job_details = {
            "job_id": job.get('job_id'),
            "title": job.get('title'),
            "company": job.get('company'),
            "location": job.get('location', ''),
            "description": job.get('description', ''),
            "seniority_level": job.get('seniority_level', ''),
            "employment_type": job.get('employment_type', ''),
            "job_function": job.get('job_function', ''),
            "industries": job.get('industries', ''),
            "skills": skills_list,
            "role_tag": job.get('role_tag', ''),
            "role_key": job.get('role_key', ''),
            "posted_date": job.get('posted_date', ''),
            "job_url": job.get('job_url', '')
        }
        
        logger.info(f"Retrieved job details for {job_id}")
        return job_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job details for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job details: {str(e)}"
        )
