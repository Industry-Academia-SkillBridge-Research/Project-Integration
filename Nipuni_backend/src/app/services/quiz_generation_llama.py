"""
Quiz generation service using Ollama LLM and quiz plans.
Uses flat skill structure - no parent/child hierarchy.
"""

import json
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.quiz import QuizPlan, QuizAttempt, QuizQuestion
from ..services.ollama_client import generate_mcq, DEFAULT_MODEL

logger = logging.getLogger(__name__)


def generate_quiz_from_latest_plan(
    student_id: str,
    db: Session,
    model: str = DEFAULT_MODEL
) -> dict:
    """
    Generate quiz questions from the latest quiz plan using Ollama.
    
    Args:
        student_id: Student identifier
        db: Database session
        model: Ollama model to use
        
    Returns:
        Dictionary with attempt_id and questions (without answers)
        
    Raises:
        HTTPException: If no plan found or generation fails
    """
    logger.info(f"Generating quiz for student {student_id} using model {model}")
    
    # Load latest quiz plan
    quiz_plan = db.query(QuizPlan).filter(
        QuizPlan.student_id == student_id
    ).order_by(QuizPlan.created_at.desc()).first()
    
    if not quiz_plan:
        raise HTTPException(
            status_code=404,
            detail=f"No quiz plan found for student {student_id}"
        )
    
    # Parse plan data
    try:
        skills_list = json.loads(quiz_plan.skills_json)
        difficulty_mix_dict = json.loads(quiz_plan.difficulty_mix_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse quiz plan JSON: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Invalid quiz plan data"
        )
    
    logger.info(f"Quiz plan loaded: {len(skills_list)} skills, plan_id={quiz_plan.id}")
    
    # Create quiz attempt
    quiz_attempt = QuizAttempt(
        student_id=student_id,
        model_used=model,
        created_at=datetime.utcnow()
    )
    db.add(quiz_attempt)
    db.commit()
    db.refresh(quiz_attempt)
    
    attempt_id = quiz_attempt.attempt_id
    logger.info(f"Created quiz attempt {attempt_id}")
    
    # Generate questions
    generated_questions = []
    warnings = []
    
    for skill_name in skills_list:
        # Get difficulty mix for this skill
        difficulty_mix = difficulty_mix_dict.get(skill_name, {"easy": 2, "medium": 1, "hard": 1})
        
        logger.info(
            f"Generating questions for skill '{skill_name}': {difficulty_mix}"
        )
        
        # Generate questions for each difficulty level
        for difficulty, count in difficulty_mix.items():
            for i in range(count):
                # For flat skills, use the skill name directly as scope
                scope_for_question = [skill_name]
                
                logger.info(
                    f"Generating question {i+1}/{count} for skill={skill_name}, "
                    f"difficulty={difficulty}"
                )
                
                try:
                    # Generate MCQ using Ollama
                    mcq_data = generate_mcq(
                        skill_name=skill_name,
                        difficulty=difficulty,
                        scope_bullets=scope_for_question,
                        model=model
                    )
                    
                    # Store in database
                    quiz_question = QuizQuestion(
                        attempt_id=attempt_id,
                        student_id=student_id,
                        skill_name=skill_name,
                        difficulty=difficulty,
                        question_text=mcq_data["question_text"],
                        options_json=json.dumps(mcq_data["options"]),
                        correct_option=mcq_data["correct_option"],
                        explanation=mcq_data["explanation"]
                    )
                    db.add(quiz_question)
                    db.flush()  # Get question_id
                    
                    # Add to response (WITHOUT correct_option or explanation)
                    generated_questions.append({
                        "question_id": quiz_question.question_id,
                        "skill_name": skill_name,
                        "difficulty": difficulty,
                        "question_text": mcq_data["question_text"],
                        "options": mcq_data["options"]  # Already a dict
                    })
                    
                    logger.debug(f"Stored question {quiz_question.question_id}")
                
                except ValueError as e:
                    # Non-fatal error - continue with other questions
                    warning_msg = f"Failed to generate question for {skill_name}/{difficulty}: {str(e)}"
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)
                    continue
                except HTTPException as e:
                    # Network/Ollama error - propagate immediately
                    raise
                except Exception as e:
                    # Unexpected error - log but continue
                    warning_msg = f"Unexpected error for {skill_name}/{difficulty}: {str(e)}"
                    logger.error(warning_msg)
                    warnings.append(warning_msg)
                    continue
    
    db.commit()
    
    logger.info(
        f"Quiz generation complete: attempt_id={attempt_id}, "
        f"{len(generated_questions)} questions generated"
    )
    
    if warnings:
        logger.warning(f"Generation completed with {len(warnings)} warnings")
    
    result = {
        "attempt_id": attempt_id,
        "questions": generated_questions
    }
    
    if warnings:
        result["warnings"] = warnings
    
    return result
