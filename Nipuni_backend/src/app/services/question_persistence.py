"""
Question Bank Persistence Layer
Exports and imports questions to/from JSON files to survive database resets.
"""
import json
import os
from pathlib import Path
from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.question_bank import QuestionBank
import logging

logger = logging.getLogger(__name__)

QUESTIONS_DIR = Path("backend/data/knowledge_base/questions")
QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)


def export_questions_to_json(db: Session, output_dir: str = None) -> Dict[str, int]:
    """
    Export all questions from database to JSON files (one file per skill).
    
    Args:
        db: Database session
        output_dir: Directory to save JSON files (default: data/knowledge_base/questions)
        
    Returns:
        Dictionary with export statistics
    """
    if output_dir is None:
        output_dir = QUESTIONS_DIR
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all questions grouped by skill
    all_questions = db.query(QuestionBank).all()
    
    if not all_questions:
        logger.warning("No questions found in database to export")
        return {"skills_exported": 0, "questions_exported": 0}
    
    # Group by skill
    questions_by_skill = {}
    for q in all_questions:
        if q.skill_name not in questions_by_skill:
            questions_by_skill[q.skill_name] = []
        
        questions_by_skill[q.skill_name].append({
            "skill_name": q.skill_name,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "options_json": q.options_json,
            "correct_option": q.correct_option,
            "explanation": q.explanation
        })
    
    # Save each skill to its own JSON file
    skills_exported = 0
    questions_exported = 0
    
    for skill_name, questions in questions_by_skill.items():
        # Create safe filename
        safe_filename = skill_name.replace(" ", "_").replace("&", "and").replace("/", "-")
        filepath = output_dir / f"{safe_filename}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "skill_name": skill_name,
                "questions": questions,
                "total_questions": len(questions)
            }, f, indent=2, ensure_ascii=False)
        
        skills_exported += 1
        questions_exported += len(questions)
        logger.info(f"Exported {len(questions)} questions for '{skill_name}' to {filepath}")
    
    logger.info(f"✅ Export complete: {questions_exported} questions across {skills_exported} skills")
    
    return {
        "skills_exported": skills_exported,
        "questions_exported": questions_exported,
        "output_directory": str(output_dir)
    }


def import_questions_from_json(db: Session, input_dir: str = None, overwrite: bool = False) -> Dict[str, int]:
    """
    Import questions from JSON files into the database.
    
    Args:
        db: Database session
        input_dir: Directory containing JSON files (default: data/knowledge_base/questions)
        overwrite: If True, delete existing questions before importing
        
    Returns:
        Dictionary with import statistics
    """
    if input_dir is None:
        input_dir = QUESTIONS_DIR
    else:
        input_dir = Path(input_dir)
    
    if not input_dir.exists():
        logger.error(f"Questions directory not found: {input_dir}")
        return {"skills_imported": 0, "questions_imported": 0, "errors": ["Directory not found"]}
    
    # Clear existing questions if overwrite=True
    if overwrite:
        deleted = db.query(QuestionBank).delete()
        db.commit()
        logger.info(f"Deleted {deleted} existing questions from database")
    
    # Find all JSON files
    json_files = list(input_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return {"skills_imported": 0, "questions_imported": 0, "errors": ["No JSON files found"]}
    
    skills_imported = 0
    questions_imported = 0
    errors = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            skill_name = data.get("skill_name")
            questions = data.get("questions", [])
            
            if not skill_name or not questions:
                errors.append(f"Invalid format in {json_file.name}")
                continue
            
            # Insert questions
            for q_data in questions:
                # Check if question already exists
                existing = db.query(QuestionBank).filter(
                    QuestionBank.skill_name == q_data["skill_name"],
                    QuestionBank.question_text == q_data["question_text"]
                ).first()
                
                if existing and not overwrite:
                    continue  # Skip duplicates
                
                question = QuestionBank(
                    skill_name=q_data["skill_name"],
                    difficulty=q_data["difficulty"],
                    question_text=q_data["question_text"],
                    options_json=q_data["options_json"],
                    correct_option=q_data["correct_option"],
                    explanation=q_data.get("explanation", "")
                )
                db.add(question)
                questions_imported += 1
            
            db.commit()
            skills_imported += 1
            logger.info(f"✅ Imported {len(questions)} questions for '{skill_name}'")
            
        except Exception as e:
            logger.error(f"Error importing {json_file.name}: {e}")
            errors.append(f"{json_file.name}: {str(e)}")
            db.rollback()
    
    logger.info(f"✅ Import complete: {questions_imported} questions across {skills_imported} skills")
    
    return {
        "skills_imported": skills_imported,
        "questions_imported": questions_imported,
        "errors": errors if errors else None
    }


def backup_questions(db: Session) -> str:
    """
    Quick backup of all questions to JSON files.
    
    Returns:
        Path to backup directory
    """
    result = export_questions_to_json(db)
    return result.get("output_directory", str(QUESTIONS_DIR))


def restore_questions(db: Session, clear_existing: bool = True) -> Dict[str, int]:
    """
    Quick restore of all questions from JSON files.
    
    Args:
        db: Database session
        clear_existing: If True, clear all existing questions first
        
    Returns:
        Import statistics
    """
    return import_questions_from_json(db, overwrite=clear_existing)
