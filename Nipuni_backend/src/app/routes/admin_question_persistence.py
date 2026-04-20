"""
Admin routes for question bank backup/restore
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..services.question_persistence import (
    export_questions_to_json,
    import_questions_from_json,
    backup_questions,
    restore_questions
)
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/question-bank", tags=["Admin - Question Persistence"])


class BackupResponse(BaseModel):
    message: str
    skills_exported: int
    questions_exported: int
    output_directory: str


class RestoreResponse(BaseModel):
    message: str
    skills_imported: int
    questions_imported: int
    errors: Optional[list] = None


@router.post("/backup", response_model=BackupResponse)
def backup_question_bank(db: Session = Depends(get_db)):
    """
    Backup all questions to JSON files in data/knowledge_base/questions/.
    
    Run this BEFORE deleting the database to preserve your questions!
    
    Returns:
        Backup statistics
    """
    result = export_questions_to_json(db)
    
    return BackupResponse(
        message=f"Backed up {result['questions_exported']} questions to JSON files",
        skills_exported=result["skills_exported"],
        questions_exported=result["questions_exported"],
        output_directory=result["output_directory"]
    )


@router.post("/restore", response_model=RestoreResponse)
def restore_question_bank(
    clear_existing: bool = True,
    db: Session = Depends(get_db)
):
    """
    Restore questions from JSON files in data/knowledge_base/questions/.
    
    Run this AFTER creating a new database to reload your questions!
    
    Args:
        clear_existing: If true, delete all existing questions before importing
        
    Returns:
        Restore statistics
    """
    result = import_questions_from_json(db, overwrite=clear_existing)
    
    if result["questions_imported"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No question files found to restore. Generate questions first or check data/knowledge_base/questions/ directory."
        )
    
    return RestoreResponse(
        message=f"Restored {result['questions_imported']} questions from JSON files",
        skills_imported=result["skills_imported"],
        questions_imported=result["questions_imported"],
        errors=result.get("errors")
    )
