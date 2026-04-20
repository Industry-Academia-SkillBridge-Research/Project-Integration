"""
Transcript upload and processing routes.
Uses flat skill structure.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..services.transcript_service import process_transcript_upload
from ..services.transcript_processor_flat import compute_skill_scores, save_skill_profile
from ..models.student import Student
from ..models.course import CourseTaken
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcript", tags=["Transcript"])


@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    student_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a student transcript.
    
    Args:
        file: PDF transcript file
        student_id: Student identifier
        db: Database session
        
    Returns:
        Dictionary with parsed courses, warnings, and skill computation summary
    """
    try:
        logger.info(f"Processing transcript upload for student: {student_id}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Process transcript
        result = process_transcript_upload(db, file, student_id)
        
        # Auto-compute skills if courses were successfully parsed
        if result.get("parsed_courses") and len(result["parsed_courses"]) > 0:
            logger.info(f"Auto-computing flat skills for student: {student_id}")
            
            try:
                # Compute flat skills from courses
                skill_result = compute_skill_scores(db, student_id)
                logger.info(f"Computed {skill_result['total_skills']} flat skills")
                
                # Save to database
                save_skill_profile(db, student_id, skill_result)
                logger.info(f"Saved skill profile with {skill_result['total_evidence']} evidence entries")
                
                # Add skill computation info to result
                result["skills_auto_computed"] = {
                    "skills": skill_result["total_skills"],
                    "evidence": skill_result["total_evidence"]
                }
            except Exception as e:
                logger.error(f"Skill computation failed: {e}", exc_info=True)
                result["warnings"].append(f"Skill computation failed: {str(e)}")
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Transcript upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Transcript processing failed: {str(e)}"
        )


@router.get("/{student_id}")
def get_transcript(student_id: str, db: Session = Depends(get_db)):
    """
    Get transcript details for a student.
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        Dictionary with student info and courses
    """
    try:
        # Get student info
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"No transcript found for student {student_id}"
            )
        
        # Get courses
        courses = db.query(CourseTaken).filter(CourseTaken.student_id == student_id).all()
        
        return {
            "student_id": student.student_id,
            "name": student.name or "N/A",
            "program": student.program or "N/A",
            "intake": student.intake or "N/A",
            "specialization": student.specialization or "N/A",
            "courses": [
                {
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "grade": course.grade,
                    "credits": course.credits
                }
                for course in courses
            ]
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to retrieve transcript: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transcript: {str(e)}"
        )
