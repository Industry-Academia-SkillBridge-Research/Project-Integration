"""
Quiz planning service for creating personalized quiz plans based on student skills.
Uses flat skill structure.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ..models.skill import SkillProfileClaimed
from ..models.quiz import QuizPlan

logger = logging.getLogger(__name__)

MAX_SKILLS_ALLOWED = 5
QUESTIONS_PER_SKILL = 4


def determine_difficulty_mix(skill_score: float) -> Dict[str, int]:
    """
    Determine difficulty mix based on skill score.
    
    Args:
        skill_score: Skill score (0-100)
        
    Returns:
        Dictionary with difficulty distribution: {"easy": X, "medium": Y, "hard": Z}
    """
    if skill_score >= 85:
        # Advanced - more challenging questions
        return {"easy": 1, "medium": 1, "hard": 2}
    elif skill_score >= 70:
        # Intermediate - balanced mix
        return {"easy": 2, "medium": 1, "hard": 1}
    else:
        # Beginner - easier questions
        return {"easy": 2, "medium": 2, "hard": 0}


def create_quiz_plan(
    student_id: str,
    db: Session,
    selected_skills: Optional[List[str]] = None,
    max_skills: int = 5
) -> QuizPlan:
    """
    Create a quiz plan for a student based on claimed skills (flat skill structure).
    
    Args:
        student_id: Student identifier
        db: Database session
        selected_skills: Optional list of specific skill names to include
        max_skills: Maximum number of skills to include (default 5)
        
    Returns:
        Created QuizPlan object
        
    Raises:
        ValueError: If validation fails (too many skills, skill not found, etc.)
    """
    logger.info(f"Creating quiz plan for student: {student_id}")
    
    # Get claimed skills (flat skill structure)
    all_claimed_skills = db.query(SkillProfileClaimed).filter(
        SkillProfileClaimed.student_id == student_id
    ).all()
    
    if not all_claimed_skills:
        raise ValueError(f"No skills found for student {student_id}")
    
    skill_lookup = {skill.skill_name: skill for skill in all_claimed_skills}
    logger.info(f"Using claimed skills: {len(all_claimed_skills)} skills found")
    
    # Determine which skills to use
    if selected_skills is not None:
        # Manual selection mode
        if len(selected_skills) > MAX_SKILLS_ALLOWED:
            raise ValueError(
                f"Too many skills selected. Maximum allowed: {MAX_SKILLS_ALLOWED}, "
                f"got: {len(selected_skills)}"
            )
        
        # Validate all selected skills exist
        for skill_name in selected_skills:
            if skill_name not in skill_lookup:
                raise ValueError(
                    f"Skill '{skill_name}' not found for student {student_id}"
                )
        
        selected_skill_names = selected_skills
        logger.info(f"Using manually selected skills: {selected_skill_names}")
    else:
        # Auto-pick mode: sort by priority criteria
        # Priority: low confidence first, then closest to 70, then highest score
        all_skills_list = list(skill_lookup.values())
        
        sorted_skills = sorted(
            all_skills_list,
            key=lambda s: (
                s.confidence,  # ASC - low confidence = needs practice
                abs(s.claimed_score - 70),  # ASC - closest to intermediate level
                -s.claimed_score  # DESC - higher score as tiebreaker
            )
        )
        
        # Pick top skills up to max_skills
        top_skills = sorted_skills[:max_skills]
        selected_skill_names = [skill.skill_name for skill in top_skills]
        
        logger.info(
            f"Auto-selected {len(selected_skill_names)} skills based on confidence "
            f"and score: {selected_skill_names}"
        )
    
    # Build difficulty mix per skill
    difficulty_mix_per_skill = {}
    for skill_name in selected_skill_names:
        skill_obj = skill_lookup[skill_name]
        score = skill_obj.claimed_score
        
        difficulty_mix = determine_difficulty_mix(score)
        difficulty_mix_per_skill[skill_name] = difficulty_mix
        
        logger.debug(
            f"Skill: {skill_name}, Score: {score:.2f}, "
            f"Mix: {difficulty_mix}"
        )
    
    # Delete previous quiz plans for this student (or could mark as inactive)
    db.query(QuizPlan).filter(QuizPlan.student_id == student_id).delete()
    db.flush()
    
    # Create new quiz plan
    quiz_plan = QuizPlan(
        student_id=student_id,
        skill_type="claimed",  # Using flat skill structure
        skills_json=json.dumps(selected_skill_names),
        questions_per_skill=QUESTIONS_PER_SKILL,
        difficulty_mix_json=json.dumps(difficulty_mix_per_skill),
        created_at=datetime.utcnow()
    )
    
    db.add(quiz_plan)
    db.commit()
    db.refresh(quiz_plan)
    
    logger.info(
        f"Quiz plan created: {len(selected_skill_names)} skills, "
        f"{QUESTIONS_PER_SKILL} questions per skill"
    )
    
    return quiz_plan
