"""
Student Profile Routes

Handles student portfolio and profile data retrieval and updates.
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import base64

from ..db import get_db
from ..models.student_skill_portfolio import StudentSkillPortfolio
from ..models.skill import SkillProfileClaimed
from ..models.student import Student

router = APIRouter()
logger = logging.getLogger(__name__)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    program: Optional[str] = None
    specialization: Optional[str] = None


@router.get("/students/{student_id}/profile/portfolio")
def get_student_portfolio(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Get student's skill portfolio sorted by final score descending.
    
    Returns all portfolio entries showing verified quiz performance,
    claimed scores, and calculated final scores with weights.
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        List of portfolio entries with skill details and scores
    """
    try:
        # Query portfolio entries for this student, sorted by final_score desc
        portfolio = db.query(StudentSkillPortfolio).filter(
            StudentSkillPortfolio.student_id == student_id
        ).order_by(StudentSkillPortfolio.final_score.desc()).all()
        
        if not portfolio:
            logger.info(f"No portfolio data found for student {student_id}")
            return []
        
        # Convert to dict format
        portfolio_data = [
            {
                "id": entry.id,
                "student_id": entry.student_id,
                "skill_name": entry.skill_name,
                "claimed_score": round(entry.claimed_score, 2),
                "verified_score": round(entry.verified_score, 2),
                "quiz_weight": round(entry.quiz_weight, 4),
                "claimed_weight": round(entry.claimed_weight, 4),
                "final_score": round(entry.final_score, 2),
                "final_level": entry.final_level,
                "correct_count": entry.correct_count,
                "total_questions": entry.total_questions,
                "updated_at": entry.updated_at.isoformat()
            }
            for entry in portfolio
        ]
        
        logger.info(f"Retrieved {len(portfolio_data)} portfolio entries for student {student_id}")
        
        return portfolio_data
    
    except Exception as e:
        logger.error(f"Error retrieving portfolio for student {student_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve portfolio: {str(e)}"
        )


@router.get("/students/{student_id}/profile")
def get_student_profile(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete student profile including personal info and portfolio.
    """
    try:
        # Get student info
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            # Create default student record
            student = Student(student_id=student_id)
            db.add(student)
            db.commit()
            db.refresh(student)
        
        # Get portfolio (quiz-verified skills)
        portfolio = db.query(StudentSkillPortfolio).filter(
            StudentSkillPortfolio.student_id == student_id
        ).order_by(StudentSkillPortfolio.final_score.desc()).all()
        
        # Get claimed skills (from transcript, not yet verified)
        claimed_skills = db.query(SkillProfileClaimed).filter(
            SkillProfileClaimed.student_id == student_id
        ).order_by(SkillProfileClaimed.claimed_score.desc()).all()
        
        # Combine portfolio and claimed skills
        # If a skill is in portfolio, it's already verified, so skip it from claimed
        portfolio_skill_names = {p.skill_name for p in portfolio}
        
        # Calculate stats (only for verified skills - tested via quiz)
        total_skills = len(portfolio)
        all_scores = [p.final_score for p in portfolio]
        
        stats = {
            "total_skills": total_skills,
            "average_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            "advanced_count": sum(1 for p in portfolio if p.final_level == "Advanced"),
            "verified_count": len(portfolio),
            "claimed_count": 0,  # Not showing claimed skills in portfolio
            "total_questions": sum(p.total_questions for p in portfolio)
        }
        
        # Build portfolio with ONLY verified skills (tested via quiz)
        # Do NOT include claimed skills - portfolio should only show quiz-validated skills
        portfolio_data = []
        
        # Add only verified skills (from quizzes where student answered questions)
        for p in portfolio:
            portfolio_data.append({
                "skill_name": p.skill_name,
                "verified_score": round(p.verified_score, 2),
                "claimed_score": round(p.claimed_score, 2),
                "final_score": round(p.final_score, 2),
                "final_level": p.final_level,
                "correct_count": p.correct_count,
                "total_questions": p.total_questions,
                "status": "verified",
                "updated_at": p.updated_at.isoformat()
            })
        
        return {
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "program": student.program,
            "specialization": student.specialization,
            "intake": student.intake,
            "bio": student.bio,
            "photo_url": student.photo_url,
            "stats": stats,
            "portfolio": portfolio_data
        }
    except Exception as e:
        logger.error(f"Error retrieving profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/students/{student_id}/profile")
def update_student_profile(
    student_id: str,
    profile: UpdateProfileRequest,
    db: Session = Depends(get_db)
):
    """
    Update student profile information.
    """
    try:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            student = Student(student_id=student_id)
            db.add(student)
        
        # Update fields
        if profile.name is not None:
            student.name = profile.name
        if profile.email is not None:
            student.email = profile.email
        if profile.bio is not None:
            student.bio = profile.bio
        if profile.program is not None:
            student.program = profile.program
        if profile.specialization is not None:
            student.specialization = profile.specialization
        
        db.commit()
        db.refresh(student)
        
        return {
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "program": student.program,
            "specialization": student.specialization,
            "bio": student.bio
        }
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students/{student_id}/profile/photo")
async def upload_profile_photo(
    student_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload student profile photo (converts to base64).
    """
    try:
        # Read file content
        content = await file.read()
        
        # Convert to base64
        base64_image = base64.b64encode(content).decode('utf-8')
        content_type = file.content_type or "image/jpeg"
        photo_url = f"data:{content_type};base64,{base64_image}"
        
        # Update student record
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            student = Student(student_id=student_id)
            db.add(student)
        
        student.photo_url = photo_url
        db.commit()
        
        return {"photo_url": photo_url}
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/students/{student_id}/profile/portfolio")
def clear_student_portfolio(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear only portfolio/verified skill data for a student.
    
    This removes ONLY verified quiz results, keeping the claimed skills
    computed from the transcript. This allows students to retake quizzes
    without losing their base skill profile.
    
    Clears:
    - student_skill_portfolio (new portfolio system)
    - skill_profile_verified_parent (legacy verified skills)
    - skill_profile_final_parent (legacy final scores)
    
    Preserves:
    - skill_profile_claimed (base skills from transcript)
    - skill_evidence (course evidence)
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        Success message with count of deleted records
    """
    try:
        total_deleted = 0
        
        # Delete from student_skill_portfolio (new system)
        deleted = db.execute(
            "DELETE FROM student_skill_portfolio WHERE student_id = :sid",
            {"sid": student_id}
        )
        total_deleted += deleted.rowcount
        
        # Delete from skill_profile_verified_parent (legacy)
        deleted = db.execute(
            "DELETE FROM skill_profile_verified_parent WHERE student_id = :sid",
            {"sid": student_id}
        )
        total_deleted += deleted.rowcount
        
        # Delete from skill_profile_final_parent (legacy)
        deleted = db.execute(
            "DELETE FROM skill_profile_final_parent WHERE student_id = :sid",
            {"sid": student_id}
        )
        total_deleted += deleted.rowcount
        
        db.commit()
        
        logger.info(f"Cleared {total_deleted} portfolio records for student {student_id} (preserved claimed skills)")
        
        return {
            "message": f"Successfully cleared portfolio for student {student_id}. Claimed skills from transcript preserved.",
            "deleted_count": total_deleted
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing portfolio for student {student_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear portfolio: {str(e)}"
        )
