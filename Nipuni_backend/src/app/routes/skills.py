"""
Skills API routes for claimed skills and explainability.
Uses flat skill structure.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.skill import SkillProfileClaimed, SkillEvidence
from ..services.transcript_processor_flat import compute_skill_scores, save_skill_profile
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Skills"])


@router.get("/{student_id}/skills/claimed")
def get_claimed_skills(student_id: str, db: Session = Depends(get_db)):
    """
    Get all claimed skills for a student (flat skill structure).
    
    Computes skills on-the-fly from transcript data using course-skill mappings.
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        Dictionary with claimed skills and scores
    """
    # Compute skills using flat structure
    result = compute_skill_scores(db, student_id)
    
    if result["total_skills"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No courses or skill mappings found for student {student_id}"
        )
    
    # Format for frontend
    claimed_skills = [
        {
            "skill_name": skill_name,
            "claimed_score": data["score"],
            "claimed_level": data["level"],
            "confidence": data["confidence"],
            "evidence_count": data["evidence_count"],
            "category": data.get("category", "General"),
            "courses": data.get("courses", [])
        }
        for skill_name, data in result["skills"].items()
    ]
    
    return {
        "student_id": student_id,
        "claimed_skills": claimed_skills,
        "skills_computed": result["total_skills"],
        "evidence_count": result["total_evidence"]
    }


@router.get("/{student_id}/explain/skill/{skill_name}")
def explain_skill(
    student_id: str,
    skill_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed evidence breakdown for a specific skill.
    
    Shows skill summary and all courses that contributed to the skill score,
    sorted by contribution (highest first).
    
    Args:
        student_id: Student identifier
        skill_name: Name of the skill to explain
        db: Database session
        
    Returns:
        Dictionary with skill summary and evidence list
    """
    # Fetch skill summary
    skill_summary = db.query(SkillProfileClaimed).filter(
        SkillProfileClaimed.student_id == student_id,
        SkillProfileClaimed.skill_name == skill_name
    ).first()
    
    if not skill_summary:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found for student {student_id}"
        )
    
    # Fetch evidence sorted by contribution descending
    evidence = db.query(SkillEvidence).filter(
        SkillEvidence.student_id == student_id,
        SkillEvidence.skill_name == skill_name
    ).order_by(SkillEvidence.contribution.desc()).all()
    
    return {
        "skill_summary": {
            "skill_name": skill_summary.skill_name,
            "claimed_score": skill_summary.claimed_score,
            "claimed_level": skill_summary.claimed_level,
            "confidence": skill_summary.confidence
        },
        "evidence": [
            {
                "course_code": e.course_code,
                "grade": e.grade,
                "credits": e.credits,
                "map_weight": e.map_weight,
                "academic_year": e.academic_year,
                "recency": e.recency,
                "contribution": e.contribution
            }
            for e in evidence
        ]
    }


@router.post("/{student_id}/skills/recompute")
def recompute_skills(student_id: str, db: Session = Depends(get_db)):
    """
    Force recomputation of flat skills for a student.
    
    Useful after transcript updates.
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        Computation summary
    """
    result = compute_skill_scores(db, student_id)
    
    if result["total_skills"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No courses or skill mappings found for student {student_id}"
        )
    
    # Save the computed skills
    save_skill_profile(db, student_id, result)
    
    return {
        "status": "ok",
        "message": f"Recomputed flat skills for student {student_id}",
        "skills_computed": result["total_skills"],
        "evidence_count": result["total_evidence"]
    }
