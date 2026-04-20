"""
Quiz API routes for quiz planning and management.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.quiz import QuizPlan, QuizQuestion, QuizAttempt
from ..schemas.quiz import (
    QuizPlanRequest, QuizPlanOut,
    QuizGenerateRequest, QuizGenerateResponse, QuizQuestionOut,
    QuizSubmitResponse
)
from ..schemas.quiz_submit import QuizSubmitRequest
from ..services.quiz_planner import create_quiz_plan
from ..services.quiz_generation_llama import generate_quiz_from_latest_plan
from ..services import question_bank_service
from ..services.quiz_scoring_service import score_quiz_attempt
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Quiz"])


@router.post("/{student_id}/quiz/plan", response_model=QuizPlanOut)
def create_student_quiz_plan(
    student_id: str,
    request: QuizPlanRequest = QuizPlanRequest(),
    db: Session = Depends(get_db)
):
    """
    Create a quiz plan for a student based on parent skills.
    
    If selected_skills is provided, uses those specific skills (max 5).
    Otherwise, auto-selects skills based on confidence and score.
    
    Args:
        student_id: Student identifier
        request: Quiz plan request with optional selected_skills
        db: Database session
        
    Returns:
        Created quiz plan object
    """
    try:
        quiz_plan = create_quiz_plan(
            student_id=student_id,
            db=db,
            selected_skills=request.selected_skills
        )
        
        logger.info(f"Quiz plan created for student {student_id}")
        return quiz_plan
        
    except ValueError as e:
        logger.warning(f"Quiz plan creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating quiz plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create quiz plan")


@router.get("/{student_id}/quiz/plan/latest", response_model=QuizPlanOut)
def get_latest_quiz_plan(student_id: str, db: Session = Depends(get_db)):
    """
    Get the latest quiz plan for a student.
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        Latest quiz plan object
    """
    quiz_plan = db.query(QuizPlan).filter(
        QuizPlan.student_id == student_id
    ).order_by(QuizPlan.created_at.desc()).first()
    
    if not quiz_plan:
        raise HTTPException(
            status_code=404,
            detail=f"No quiz plan found for student {student_id}"
        )
    
    return quiz_plan


@router.post("/{student_id}/quiz/generate", response_model=QuizGenerateResponse)
def generate_quiz(
    student_id: str,
    request: QuizGenerateRequest = QuizGenerateRequest(),
    db: Session = Depends(get_db)
):
    """
    Generate quiz questions from the latest quiz plan using Ollama.
    
    Args:
        student_id: Student identifier
        request: Generation request with optional model selection
        db: Database session
        
    Returns:
        Quiz attempt with generated questions (without answers)
    """
    try:
        result = generate_quiz_from_latest_plan(
            student_id=student_id,
            db=db,
            model=request.model
        )
        
        logger.info(
            f"Quiz generated for student {student_id}: "
            f"attempt_id={result['attempt_id']}, {len(result['questions'])} questions"
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (404, 503, etc.)
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")


@router.get("/{student_id}/quiz/{attempt_id}", response_model=QuizGenerateResponse)
def get_quiz_attempt(
    student_id: str,
    attempt_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored quiz questions for a specific attempt (without answers).
    
    Args:
        student_id: Student identifier
        attempt_id: Quiz attempt identifier
        db: Database session
        
    Returns:
        Quiz questions without correct answers or explanations
    """
    # Fetch all questions for this attempt
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.attempt_id == attempt_id,
        QuizQuestion.student_id == student_id
    ).all()
    
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No quiz found for attempt_id {attempt_id}"
        )
    
    # Build response without answers
    question_list = []
    for q in questions:
        question_list.append({
            "question_id": q.question_id,
            "skill_name": q.skill_name,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "options": json.loads(q.options_json)
        })
    
    return {
        "attempt_id": attempt_id,
        "questions": question_list
    }


@router.post("/{student_id}/quiz/from-bank", response_model=QuizGenerateResponse)
def generate_quiz_from_bank(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate a quiz INSTANTLY by sampling from the QuestionBank.
    
    Uses the latest quiz plan for the student and samples pre-generated questions.
    **This is FAST** - no Ollama calls, just database queries.
    
    Steps:
    1. Get latest QuizPlan for student
    2. Sample questions from QuestionBank based on plan's skill/difficulty requirements
    3. Create QuizAttempt and QuizQuestion records
    4. Return attempt_id
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        QuizGenerateResponse with attempt_id, question count, and any warnings
    """
    try:
        # Get latest quiz plan
        quiz_plan = db.query(QuizPlan).filter(
            QuizPlan.student_id == student_id
        ).order_by(QuizPlan.created_at.desc()).first()
        
        if not quiz_plan:
            raise HTTPException(
                status_code=404,
                detail=f"No quiz plan found for student {student_id}. Create a plan first."
            )
        
        # Parse plan JSON fields
        skills = json.loads(quiz_plan.skills_json) if quiz_plan.skills_json else []
        difficulty_mix = json.loads(quiz_plan.difficulty_mix_json) if quiz_plan.difficulty_mix_json else {}
        
        # Validate skills
        if not skills:
            raise HTTPException(
                status_code=404,
                detail="QuizPlan has no skills_json"
            )
        
        # Build default difficulty mix if empty
        if not difficulty_mix:
            difficulty_mix = {skill: {"easy": 2, "medium": 1, "hard": 1} for skill in skills}
        
        questions_per_skill = quiz_plan.questions_per_skill
        
        # Build skill-difficulty requirements
        skill_difficulty_requirements = []
        for skill in skills:
            skill_difficulty_mix = difficulty_mix.get(skill, {"easy": 2, "medium": 1, "hard": 1})
            
            # Add entries for each difficulty based on count
            for difficulty, count in skill_difficulty_mix.items():
                if count > 0:
                    skill_difficulty_requirements.append({
                        "skill_name": skill,
                        "difficulty": difficulty
                    })
        
        # Sample questions from bank (may raise HTTPException(400) if no questions)
        sample_result = question_bank_service.sample_quiz_from_bank(
            db=db,
            skill_difficulty_requirements=skill_difficulty_requirements,
            questions_per_skill=1  # 1 question per skill-difficulty combination
        )
        
        questions_data = sample_result["questions"]
        warnings = sample_result.get("warnings", [])
        
        # Create QuizAttempt
        quiz_attempt = QuizAttempt(
            student_id=student_id,
            model_used="QuestionBank (pre-generated)"
        )
        db.add(quiz_attempt)
        db.flush()  # Get attempt_id
        
        # Create QuizQuestion records
        for idx, q_data in enumerate(questions_data, start=1):
            quiz_question = QuizQuestion(
                attempt_id=quiz_attempt.attempt_id,
                student_id=student_id,
                skill_name=q_data["skill_name"],
                difficulty=q_data["difficulty"],
                question_text=q_data["question"],
                options_json=json.dumps(q_data["options"]),
                correct_option=q_data["correct_option"],
                explanation=q_data["explanation"]
            )
            db.add(quiz_question)
        
        db.commit()
        
        logger.info(f"Quiz generated from bank for student {student_id}: {len(questions_data)} questions")
        
        # Log warnings if any
        if warnings:
            warnings_message = "; ".join([w.get("message", "") for w in warnings])
            logger.warning(f"Quiz generation warnings for student {student_id}: {warnings_message}")
        
        # Query back the created questions to build response (without answers)
        created_questions = db.query(QuizQuestion).filter(
            QuizQuestion.attempt_id == quiz_attempt.attempt_id
        ).all()
        
        # Build response questions list (without correct_option and explanation)
        question_list = []
        for q in created_questions:
            question_list.append({
                "question_id": q.question_id,
                "skill_name": q.skill_name,
                "difficulty": q.difficulty,
                "question_text": q.question_text,
                "options": json.loads(q.options_json)
            })
        
        return QuizGenerateResponse(
            attempt_id=quiz_attempt.attempt_id,
            questions=question_list
        )
    
    except HTTPException:
        # Re-raise HTTPExceptions (404, 400, etc.)
        raise
    except Exception as e:
        # Catch any other errors and return as 500 with detail
        logger.error(f"Error generating quiz from bank for student {student_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz from bank: {str(e)}"
        )


@router.post("/{student_id}/quiz/{attempt_id}/submit")
def submit_quiz(
    student_id: str,
    attempt_id: int,
    request: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submit quiz answers and receive scoring results.
    
    Validates answers, calculates scores per skill, updates verified and final skill profiles.
    Allows resubmission - previous answers for this attempt are deleted.
    
    Args:
        student_id: Student identifier
        attempt_id: Quiz attempt ID
        request: Quiz answers (list of question_id and selected_option)
        db: Database session
        
    Returns:
        JSON with attempt_id, overall_verified_score, and per_skill breakdown
    """
    # Validate answers list is not empty
    if not request.answers:
        raise HTTPException(
            status_code=400,
            detail="Answers list cannot be empty"
        )
    
    try:
        # Convert Pydantic models to dict format for service
        answers = [{"question_id": ans.question_id, "selected_option": ans.selected_option} 
                   for ans in request.answers]
        
        # Score the attempt and update profiles
        result = score_quiz_attempt(
            student_id=student_id,
            attempt_id=attempt_id,
            answers=answers,
            db=db
        )
        
        logger.info(f"Quiz submitted for student {student_id}, attempt {attempt_id}")
        
        return result
    
    except ValueError as e:
        # Parse error message to determine status code
        error_msg = str(e)
        
        # 404 if attempt not found
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        # 400 for invalid question_ids
        elif "Invalid question_id" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        # Catch any other errors
        logger.error(f"Error submitting quiz for student {student_id}, attempt {attempt_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit quiz: {str(e)}"
        )

