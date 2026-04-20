"""
XAI (Explainable AI) API routes for skill score explanations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..services.xai_service import (
    get_skill_explanation,
    get_all_skills_summary
)

router = APIRouter(prefix="/students/{student_id}/xai", tags=["XAI"])


@router.get("/skills/summary")
def get_skills_explanation_summary(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Get summary of all parent skills with brief explanations of top contributors.
    
    This provides a quick overview of what courses/child skills contributed most
    to each parent skill score.
    """
    try:
        result = get_all_skills_summary(db, student_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get skills summary: {str(e)}")


@router.get("/skills/{skill_name}/explain")
def explain_skill_score(
    student_id: str,
    skill_name: str,
    skill_type: str = Query("parent", pattern="^(parent|child)$"),
    db: Session = Depends(get_db)
):
    """
    Get detailed explanation of how a specific skill score was calculated.
    
    Args:
        student_id: Student ID
        skill_name: Name of the skill (e.g., "Machine Learning & Optimization")
        skill_type: "parent" or "child" skill type
        
    Returns:
        Detailed breakdown including:
        - Contributing courses
        - Child skills (for parent skills)
        - Calculation formula
        - Component weights
        - Grade/recency impacts
    """
    try:
        explanation = get_skill_explanation(db, student_id, skill_name, skill_type)
        
        if "error" in explanation:
            raise HTTPException(status_code=404, detail=explanation["error"])
        
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain skill: {str(e)}")


@router.get("/parent-skills/{parent_skill}/breakdown")
def get_parent_skill_breakdown(
    student_id: str,
    parent_skill: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed breakdown of a parent skill showing:
    - All contributing child skills
    - Course-level evidence
    - Contribution percentages
    
    This is a convenience endpoint equivalent to explain_skill_score with skill_type=parent.
    """
    try:
        explanation = get_skill_explanation(db, student_id, parent_skill, "parent")
        
        if "error" in explanation:
            raise HTTPException(status_code=404, detail=explanation["error"])
        
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get breakdown: {str(e)}")
