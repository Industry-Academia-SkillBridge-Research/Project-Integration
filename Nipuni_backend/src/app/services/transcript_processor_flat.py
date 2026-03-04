"""
Simplified Transcript Processing Service - Flat Skill Structure

Computes skill scores directly from course-skill mappings.
No parent/child hierarchy.
Includes skill categorization and advanced scoring thresholds.
"""

import pandas as pd
from sqlalchemy.orm import Session
from typing import Dict, List
import logging
from pathlib import Path

from app.models.course import CourseTaken, CourseSkillMap
from app.models.skill import SkillProfileClaimed, SkillEvidence

logger = logging.getLogger(__name__)

# Grade normalization
GRADE_MAP = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0, "W": 0.0, "I": 0.0
}

# Skill category cache
_CATEGORY_CACHE = None


def load_skill_categories() -> Dict[str, str]:
    """Load skill categories from CSV file."""
    global _CATEGORY_CACHE
    
    if _CATEGORY_CACHE is not None:
        return _CATEGORY_CACHE
    
    try:
        # Get path to skill_categories.csv
        base_dir = Path(__file__).parent.parent.parent.parent
        csv_path = base_dir / "data" / "skill_categories.csv"
        
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            _CATEGORY_CACHE = dict(zip(df['skill_name'], df['category']))
            logger.info(f"Loaded {len(_CATEGORY_CACHE)} skill categories")
        else:
            logger.warning(f"Skill categories file not found: {csv_path}")
            _CATEGORY_CACHE = {}
    except Exception as e:
        logger.error(f"Error loading skill categories: {e}")
        _CATEGORY_CACHE = {}
    
    return _CATEGORY_CACHE


def get_skill_category(skill_name: str) -> str:
    """Get category for a skill, with fallback to 'General'."""
    categories = load_skill_categories()
    return categories.get(skill_name, "General")


def normalize_grade(grade: str) -> float:
    """Convert letter grade to normalized score (0-1 range)"""
    gpa = GRADE_MAP.get(grade.upper(), 0.0)
    return gpa / 4.0  # Convert to 0-1 scale


def calculate_recency(academic_year: int, current_year: int = 2026) -> float:
    """Calculate recency factor (more recent = higher weight)"""
    if academic_year is None:
        return 0.5  # Default for unknown
    
    years_ago = current_year - academic_year
    if years_ago <= 0:
        return 1.0
    elif years_ago == 1:
        return 0.9
    elif years_ago == 2:
        return 0.8
    elif years_ago == 3:
        return 0.7
    else:
        return 0.6


def compute_skill_scores(db: Session, student_id: str) -> Dict:
    """
    Compute skill scores from transcript using flat skill structure.
    
    Uses formula: score = (Σ contributions / Σ evidence_weights) × 100
    
    Where:
    - contribution = course_skill_weight × credits × grade_norm × recency
    - evidence_weight = course_skill_weight × credits × recency
    
    Returns:
        Dict with skill scores and evidence
    """
    # Get student's courses
    courses = db.query(CourseTaken).filter(
        CourseTaken.student_id == student_id
    ).all()
    
    if not courses:
        logger.warning(f"No courses found for student {student_id}")
        return {
            "student_id": student_id,
            "skills": {},
            "total_skills": 0,
            "total_evidence": 0
        }
    
    # Get course-skill mappings
    course_codes = [c.course_code for c in courses]
    mappings = db.query(CourseSkillMap).filter(
        CourseSkillMap.course_code.in_(course_codes)
    ).all()
    
    if not mappings:
        logger.warning(f"No skill mappings found for student courses")
        return {
            "student_id": student_id,
            "skills": {},
            "total_skills": 0,
            "total_evidence": 0
        }
    
    # Build course dict for easy lookup
    course_dict = {c.course_code: c for c in courses}
    
    # Aggregate skill scores
    skill_data = {}  # skill_name -> {contributions: [], evidence_weights: []}
    all_evidence = []
    
    for mapping in mappings:
        course = course_dict.get(mapping.course_code)
        if not course:
            continue
        
        # Calculate components
        grade_norm = normalize_grade(course.grade)
        credits = course.credits or 3.0
        recency = calculate_recency(course.academic_year)
        map_weight = mapping.map_weight
        
        # Calculate contribution and evidence weight
        contribution = map_weight * credits * grade_norm * recency
        evidence_weight = map_weight * credits * recency
        
        # Store for aggregation
        if mapping.skill_name not in skill_data:
            skill_data[mapping.skill_name] = {
                "contributions": [],
                "evidence_weights": [],
                "evidence_list": []
            }
        
        skill_data[mapping.skill_name]["contributions"].append(contribution)
        skill_data[mapping.skill_name]["evidence_weights"].append(evidence_weight)
        
        # Record evidence
        evidence_entry = {
            "skill_name": mapping.skill_name,
            "course_code": course.course_code,
            "map_weight": map_weight,
            "credits": credits,
            "grade": course.grade,
            "grade_norm": grade_norm,
            "academic_year": course.academic_year,
            "recency": recency,
            "evidence_weight": evidence_weight,
            "contribution": contribution
        }
        
        skill_data[mapping.skill_name]["evidence_list"].append(evidence_entry)
        all_evidence.append(evidence_entry)
    
    # Calculate final scores
    skill_scores = {}
    for skill_name, data in skill_data.items():
        total_contribution = sum(data["contributions"])
        total_evidence = sum(data["evidence_weights"])
        
        if total_evidence > 0:
            score = (total_contribution / total_evidence) * 100.0
        else:
            score = 0.0
        
        # Determine level using advanced scoring thresholds
        # Based on previous strong scoring method: <50 = Beginner, 50-75 = Intermediate, >75 = Advanced
        if score >= 75:
            level = "Advanced"
        elif score >= 50:
            level = "Intermediate"
        else:
            level = "Beginner"
        
        # Calculate confidence (based on evidence weight and count)
        # Higher confidence requires both sufficient evidence and high weights
        max_possible_evidence = len(data["contributions"]) * 3.0  # Max credits per course
        evidence_confidence = min(total_evidence / max(max_possible_evidence, 1.0), 1.0)
        count_confidence = min(len(data["contributions"]) / 5.0, 1.0)  # 5+ courses = max confidence
        confidence = (evidence_confidence + count_confidence) / 2.0
        
        # Get category
        category = get_skill_category(skill_name)
        
        # Extract course codes and grades for quick reference
        courses = [{
            "code": ev["course_code"],
            "grade": ev["grade"],
            "contribution": round(ev["contribution"], 2)
        } for ev in data["evidence_list"]]
        
        # Sort by contribution (highest first)
        courses.sort(key=lambda x: x["contribution"], reverse=True)
        
        skill_scores[skill_name] = {
            "score": round(score, 2),
            "level": level,
            "confidence": round(confidence, 3),
            "evidence_count": len(data["contributions"]),
            "category": category,
            "courses": courses,
            "evidence": data["evidence_list"]
        }
    
    logger.info(f"Computed {len(skill_scores)} skills for student {student_id}")
    
    return {
        "student_id": student_id,
        "skills": skill_scores,
        "total_skills": len(skill_scores),
        "total_evidence": len(all_evidence)
    }


def save_skill_profile(db: Session, student_id: str, skill_scores: Dict):
    """
    Save computed skill scores to database.
    
    Saves to:
    - skill_profile_claimed (summary)
    - skill_evidence (detailed evidence)
    """
    # Clear existing data
    db.query(SkillProfileClaimed).filter(
        SkillProfileClaimed.student_id == student_id
    ).delete()
    
    db.query(SkillEvidence).filter(
        SkillEvidence.student_id == student_id
    ).delete()
    
    # Save skill profiles
    for skill_name, data in skill_scores["skills"].items():
        profile = SkillProfileClaimed(
            student_id=student_id,
            skill_name=skill_name,
            claimed_score=data["score"],
            claimed_level=data["level"],
            confidence=data["confidence"]
        )
        db.add(profile)
        
        # Save evidence
        for evidence in data["evidence"]:
            evidence_entry = SkillEvidence(
                student_id=student_id,
                skill_name=skill_name,
                course_code=evidence["course_code"],
                map_weight=evidence["map_weight"],
                credits=evidence["credits"],
                grade=evidence["grade"],
                grade_norm=evidence["grade_norm"],
                academic_year=evidence["academic_year"],
                recency=evidence["recency"],
                evidence_weight=evidence["evidence_weight"],
                contribution=evidence["contribution"]
            )
            db.add(evidence_entry)
    
    db.commit()
    logger.info(f"Saved {len(skill_scores['skills'])} skill profiles for student {student_id}")
