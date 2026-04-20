"""
ML-Based Job Recommendation Service

Enhanced job recommendation using machine learning models, verified skills,
skill levels, and skill gap analysis.

Updated for flat skill structure.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.skill import SkillProfileClaimed
from ..models.student_skill_portfolio import StudentSkillPortfolio
import logging
import pickle
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
JOB_FEATURES_FILE = DATA_DIR / "job_parent_skill_features.csv"
ROLE_MODEL_FILE = MODELS_DIR / "role_model.pkl"
FEATURE_COLUMNS_FILE = MODELS_DIR / "feature_columns.json"

# Cache
_job_features_cache = None
_ml_model_cache = None
_feature_columns_cache = None


def normalize_skill_name(value: str) -> str:
    """
    Normalize a skill name for case-insensitive and variant matching.
    
    Handles:
    - Case differences: 'Python' -> 'python'
    - Whitespace: leading/trailing and multiple spaces
    - Special characters: replaces _ and - with spaces
    - Common variants: 'ci/cd' and 'ci_cd' -> 'ci cd', 'machine-learning' -> 'machine learning'
    
    Args:
        value: Raw skill name
        
    Returns:
        Normalized skill name
    """
    if not isinstance(value, str):
        return ""
    
    # Lowercase
    normalized = value.lower()
    
    # Normalize common variants
    normalized = normalized.replace("ci/cd", "ci cd")
    normalized = normalized.replace("cicd", "ci cd")
    normalized = normalized.replace("c++", "cpp")
    normalized = normalized.replace("c#", "csharp")
    normalized = normalized.replace("node.js", "nodejs")
    normalized = normalized.replace("node js", "nodejs")
    normalized = normalized.replace("machine-learning", "machine learning")
    normalized = normalized.replace("machine_learning", "machine learning")
    
    # Replace underscores and hyphens with spaces
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("-", " ")
    
    # Strip and collapse multiple spaces
    normalized = " ".join(normalized.split())
    
    return normalized


def load_ml_model() -> Optional[any]:
    """
    Load the pre-trained ML model for job role prediction.
    
    Returns:
        Trained model object or None if not available
    """
    global _ml_model_cache
    
    if _ml_model_cache is not None:
        return _ml_model_cache
    
    if not ROLE_MODEL_FILE.exists():
        logger.warning(
            f"ML model not found at {ROLE_MODEL_FILE}. "
            "Using cosine similarity fallback. "
            "Recommendations will still work but may be less accurate."
        )
        return None
    
    try:
        with open(ROLE_MODEL_FILE, 'rb') as f:
            _ml_model_cache = pickle.load(f)
        logger.info(f"ML model loaded successfully from {ROLE_MODEL_FILE}")
        return _ml_model_cache
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
        return None


def load_feature_columns() -> Optional[List[str]]:
    """
    Load feature column names used for ML model.
    
    Returns:
        List of feature column names or None
    """
    global _feature_columns_cache
    
    if _feature_columns_cache is not None:
        return _feature_columns_cache
    
    if not FEATURE_COLUMNS_FILE.exists():
        logger.warning(f"Feature columns file not found at {FEATURE_COLUMNS_FILE}")
        return None
    
    try:
        import json
        with open(FEATURE_COLUMNS_FILE, 'r') as f:
            _feature_columns_cache = json.load(f)
        logger.info(f"Feature columns loaded: {len(_feature_columns_cache)} features")
        return _feature_columns_cache
    except Exception as e:
        logger.error(f"Failed to load feature columns: {e}")
        return None


def load_jobs_feature_table() -> pd.DataFrame:
    """
    Load job parent skill features from CSV.
    
    Returns:
        DataFrame with job skill requirements
    """
    global _job_features_cache
    
    if _job_features_cache is not None:
        return _job_features_cache
    
    if not JOB_FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"Job features file not found: {JOB_FEATURES_FILE}\n"
            f"Run: python scripts/build_job_parent_features.py"
        )
    
    logger.info(f"Loading job features from {JOB_FEATURES_FILE}")
    df = pd.read_csv(JOB_FEATURES_FILE)
    _job_features_cache = df
    logger.info(f"Loaded {len(df):,} jobs with {len(df.columns)} columns")
    return df


def get_student_skill_profile(
    db: Session,
    student_id: str,
    prefer_verified: bool = True
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Get student's skill scores and levels (flat skill structure).
    
    Prioritizes portfolio (tested) skills over claimed skills.
    Uses normalized skill names for matching.
    
    Args:
        db: Database session
        student_id: Student identifier
        prefer_verified: If True, use portfolio (verified) skills when available
        
    Returns:
        Tuple of (skill_scores dict, skill_levels dict)
        Keys are normalized skill names
    """
    skill_scores = {}
    skill_levels = {}
    verified_count = 0
    claimed_count = 0
    
    # Get verified skills from portfolio (tested via quiz)
    portfolio_skills = db.query(StudentSkillPortfolio).filter(
        StudentSkillPortfolio.student_id == student_id
    ).all()
    
    if portfolio_skills and prefer_verified:
        logger.info(f"Using {len(portfolio_skills)} portfolio skills for {student_id}")
        for skill in portfolio_skills:
            normalized_name = normalize_skill_name(skill.skill_name)
            
            # Keep higher score if duplicate normalized names
            if normalized_name in skill_scores:
                if skill.final_score > skill_scores[normalized_name]:
                    skill_scores[normalized_name] = skill.final_score
                    skill_levels[normalized_name] = skill.final_level
            else:
                skill_scores[normalized_name] = skill.final_score
                skill_levels[normalized_name] = skill.final_level
        verified_count = len(portfolio_skills)
    
    # Get claimed skills (from transcript) if no portfolio skills OR to supplement
    claimed_skills = db.query(SkillProfileClaimed).filter(
        SkillProfileClaimed.student_id == student_id
    ).all()
    
    # Add claimed skills only for skills NOT in normalized portfolio
    for skill in claimed_skills:
        normalized_name = normalize_skill_name(skill.skill_name)
        
        # Skip if already have better score from portfolio
        if normalized_name in skill_scores:
            if skill.claimed_score > skill_scores[normalized_name]:
                skill_scores[normalized_name] = skill.claimed_score
                # Infer level from score
                if skill.claimed_score >= 75:
                    skill_levels[normalized_name] = "Advanced"
                elif skill.claimed_score >= 50:
                    skill_levels[normalized_name] = "Intermediate"
                else:
                    skill_levels[normalized_name] = "Beginner"
        else:
            skill_scores[normalized_name] = skill.claimed_score
            # Infer level from score if not in portfolio
            if skill.claimed_score >= 75:
                skill_levels[normalized_name] = "Advanced"
            elif skill.claimed_score >= 50:
                skill_levels[normalized_name] = "Intermediate"
            else:
                skill_levels[normalized_name] = "Beginner"
            claimed_count += 1
    
    logger.info(
        f"Student profile: {len(skill_scores)} total skills (normalized) "
        f"({verified_count} verified from quizzes, {claimed_count} claimed from transcript)"
    )
    
    return skill_scores, skill_levels


def calculate_skill_gap(
    student_scores: Dict[str, float],
    student_levels: Dict[str, str],
    job_required_skills: List[str],
    threshold: float = 70.0
) -> Dict:
    """
    Calculate skill gaps between student profile and job requirements.
    
    Normalizes skill names for lookup while preserving original display names.
    
    Args:
        student_scores: Student's skill scores (keys are normalized names)
        student_levels: Student's skill levels (keys are normalized names)
        job_required_skills: List of skills required for job (original display names)
        threshold: Minimum score to consider "proficient"
        
    Returns:
        Dictionary with matched, missing, and improvement suggestions
    """
    proficient_skills = []
    needs_improvement = []
    missing_skills = []
    
    for skill in job_required_skills:
        # Normalize skill name for lookup
        normalized_skill = normalize_skill_name(skill)
        score = student_scores.get(normalized_skill, 0.0)
        level = student_levels.get(normalized_skill, "Not Assessed")
        
        if score >= threshold:
            proficient_skills.append({
                "skill": skill,  # Keep original display name
                "score": round(score, 1),
                "level": level,
                "status": "Proficient"
            })
        elif score > 0:
            gap = threshold - score
            needs_improvement.append({
                "skill": skill,  # Keep original display name
                "score": round(score, 1),
                "level": level,
                "gap": round(gap, 1),
                "status": "Needs Improvement",
                "recommendation": _get_improvement_recommendation(score)
            })
        else:
            missing_skills.append({
                "skill": skill,  # Keep original display name
                "score": 0.0,
                "level": "Not Assessed",
                "gap": threshold,
                "status": "Missing",
                "recommendation": "Start with foundational courses"
            })
    
    return {
        "proficient": proficient_skills,
        "needs_improvement": needs_improvement,
        "missing": missing_skills,
        "match_percentage": (len(proficient_skills) / len(job_required_skills) * 100) 
                           if job_required_skills else 0
    }


def _get_improvement_recommendation(score: float) -> str:
    """Generate skill improvement recommendation based on score."""
    if score >= 60:
        return "Take advanced courses or work on real projects"
    elif score >= 40:
        return "Complete intermediate tutorials and practice exercises"
    else:
        return "Start with beginner courses and build foundations"


def calculate_weighted_match_score(
    student_scores: Dict[str, float],
    required_skills: List[str]
) -> float:
    """
    Calculate interpretable weighted match score based on student's normalized skills.
    
    Score represents the average of student's normalized scores across all required skills.
    This directly reflects how well the student performs on the job's skill requirements.
    
    Args:
        student_scores: Student's skill scores with normalized keys (0-100)
        required_skills: List of required skills for the job (original display names)
        
    Returns:
        Weighted match score (0-100), rounded to 1 decimal place
    """
    if not required_skills:
        return 0.0
    
    total_contribution = 0.0
    
    for skill in required_skills:
        normalized_skill = normalize_skill_name(skill)
        student_score = student_scores.get(normalized_skill, 0.0)
        contribution = student_score / 100.0
        total_contribution += contribution
    
    # Average contribution across all required skills
    average_contribution = total_contribution / len(required_skills)
    match_score = average_contribution * 100.0
    
    return round(match_score, 1)


def get_top_contributing_skills(
    student_scores: Dict[str, float],
    required_skills: List[str],
    limit: int = 5
) -> List[Dict]:
    """
    Get the top required skills by student score for explainability.
    
    Args:
        student_scores: Student's skill scores with normalized keys (0-100)
        required_skills: List of required skills for the job (original display names)
        limit: Maximum number of top contributors to return
        
    Returns:
        List of top skills with scores, sorted descending
    """
    skill_scores_list = []
    
    for skill in required_skills:
        normalized_skill = normalize_skill_name(skill)
        student_score = student_scores.get(normalized_skill, 0.0)
        skill_scores_list.append({
            "skill": skill,
            "score": round(student_score, 1)
        })
    
    # Sort by score descending
    skill_scores_list.sort(key=lambda x: x["score"], reverse=True)
    
    return skill_scores_list[:limit]


def recommend_jobs_ml(
    db: Session,
    student_id: str,
    top_k: int = 10,
    threshold: float = 70.0,
    use_verified: bool = True,
    role_key: Optional[str] = None
) -> List[Dict]:
    """
    ML-enhanced job recommendation with skill gap analysis.
    
    Uses normalized skill names for matching to handle case and variant differences.
    
    Args:
        db: Database session
        student_id: Student identifier
        top_k: Number of top jobs to return
        threshold: Minimum score for skill proficiency
        use_verified: Prefer verified skills over claimed
        role_key: Optional filter by role category
        
    Returns:
        List of job recommendations with detailed skill gap analysis
    """
    # Load job features
    jobs_df = load_jobs_feature_table()
    
    # Filter by role_key if specified
    if role_key:
        jobs_df = jobs_df[jobs_df['role_key'] == role_key].copy()
        if len(jobs_df) == 0:
            logger.warning(f"No jobs found for role_key: {role_key}")
            return []
    
    # Filter for entry-level and internship positions only
    if 'seniority_level' in jobs_df.columns:
        jobs_df = jobs_df[jobs_df['seniority_level'].isin(['Entry level', 'Internship'])].copy()
        logger.info(f"Filtered to {len(jobs_df)} entry-level and internship positions")
        if len(jobs_df) == 0:
            logger.warning("No entry-level or internship jobs found")
            return []
    
    # Get student skill profile (returns normalized keys)
    student_scores, student_levels = get_student_skill_profile(
        db, student_id, prefer_verified=use_verified
    )
    
    if not student_scores:
        raise ValueError(f"No skills found for student {student_id}")
    
    # Debug logging: student skills
    logger.info(f"Student {student_id} has {len(student_scores)} normalized skills")
    first_10_skills = list(student_scores.keys())[:10]
    logger.debug(f"First 10 student skills: {first_10_skills}")
    
    # Identify skill columns (exclude metadata)
    metadata_cols = ['job_id', 'title', 'company', 'role_key', 'description', 'seniority_level']
    skill_cols = [col for col in jobs_df.columns if col not in metadata_cols]
    
    # Calculate recommendations
    recommendations = []
    
    for idx, job_row in jobs_df.iterrows():
        # Get required skills (where feature = 1)
        required_skills = [
            skill for skill in skill_cols
            if job_row[skill] == 1
        ]
        
        if not required_skills:
            continue
        
        # Calculate skill gap analysis
        gap_analysis = calculate_skill_gap(
            student_scores,
            student_levels,
            required_skills,
            threshold
        )
        
        # Calculate match score using weighted skill fit
        match_score = calculate_weighted_match_score(student_scores, required_skills)
        
        # Get top contributing skills for explainability
        top_contributors = get_top_contributing_skills(student_scores, required_skills, limit=5)
        
        # Build recommendation summary
        recommendation_summary = build_recommendation_summary(gap_analysis, match_score)
        
        # Debug logging
        logger.debug(
            f"Job: {job_row['title']} | "
            f"Required skills: {len(required_skills)} | "
            f"Match score: {match_score}% | "
            f"Skill match %: {gap_analysis['match_percentage']:.1f}%"
        )
        
        # Build recommendation
        recommendations.append({
            "job_id": job_row['job_id'],
            "title": job_row['title'],
            "company": job_row['company'],
            "role_key": job_row.get('role_key', 'N/A'),
            "description": job_row.get('description', ''),
            "match_score": match_score,
            "ml_prediction": False,  # Using rule-based scoring instead
            "scoring_method": "weighted_skill_fit",
            
            # Skill analysis
            "total_required_skills": len(required_skills),
            "proficient_skills_count": len(gap_analysis["proficient"]),
            "needs_improvement_count": len(gap_analysis["needs_improvement"]),
            "missing_skills_count": len(gap_analysis["missing"]),
            "skill_match_percentage": round(gap_analysis["match_percentage"], 1),
            
            # Detailed breakdowns
            "proficient_skills": gap_analysis["proficient"],
            "needs_improvement": gap_analysis["needs_improvement"],
            "missing_skills": gap_analysis["missing"],
            "top_contributors": top_contributors,
            
            # Recommendations
            "recommendation_summary": recommendation_summary,
            "readiness": _calculate_readiness(gap_analysis),
            "next_steps": _generate_next_steps(gap_analysis)
        })
    
    # Sort by match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    logger.info(
        f"Generated {len(recommendations)} ML recommendations for {student_id}, "
        f"returning top {top_k}"
    )
    
    return recommendations[:top_k]


def _calculate_readiness(gap_analysis: Dict) -> Dict:
    """
    Calculate job readiness level.
    
    Returns:
        Dict with readiness level and score
    """
    match_pct = gap_analysis["match_percentage"]
    
    if match_pct >= 80:
        return {
            "level": "Ready to Apply",
            "score": match_pct,
            "color": "green",
            "message": "You have most required skills. Apply now!"
        }
    elif match_pct >= 60:
        return {
            "level": "Almost Ready",
            "score": match_pct,
            "color": "yellow",
            "message": "Improve a few skills and you'll be ready."
        }
    elif match_pct >= 40:
        return {
            "level": "Developing",
            "score": match_pct,
            "color": "orange",
            "message": "Focus on building missing skills."
        }
    else:
        return {
            "level": "Early Stage",
            "score": match_pct,
            "color": "red",
            "message": "This role requires significant skill development."
        }


def build_recommendation_summary(gap_analysis: Dict, match_score: float) -> str:
    """
    Build a concise, professional summary of the job recommendation.
    
    Summarizes alignment level and key action items in 1-2 sentences.
    
    Args:
        gap_analysis: Skill gap analysis dictionary
        match_score: Weighted match score (0-100)
        
    Returns:
        Professional recommendation summary string
    """
    missing_count = len(gap_analysis["missing"])
    improvement_count = len(gap_analysis["needs_improvement"])
    proficient_count = len(gap_analysis["proficient"])
    match_pct = gap_analysis.get("match_percentage", 0)
    
    # Strong match (80%+)
    if match_pct >= 80:
        total_required = proficient_count + improvement_count + missing_count
        return (
            f"This role is a strong match because you already meet {proficient_count} of the "
            f"{total_required} required skills. You're ready to apply!"
        )
    
    # Partial match (40-79%)
    elif match_pct >= 40:
        missing_skills = [s["skill"] for s in gap_analysis["missing"][:2]]
        improve_skills = [s["skill"] for s in gap_analysis["needs_improvement"][:2]]
        
        gaps = []
        if missing_skills:
            gaps.append(f"learn {', '.join(missing_skills)}")
        if improve_skills:
            gaps.append(f"strengthen {', '.join(improve_skills)}")
        
        gap_text = " and ".join(gaps) if gaps else "strengthen your skills"
        return (
            f"You are partially aligned with this role. "
            f"To become competitive, focus on {gap_text}."
        )
    
    # Early stage (< 40%)
    else:
        core_missing = [s["skill"] for s in gap_analysis["missing"][:3]]
        missing_text = ", ".join(core_missing) if core_missing else "key foundational skills"
        return (
            f"This role is currently aspirational and would require building several core skills "
            f"including {missing_text}. Start with foundational courses to prepare."
        )


def _generate_next_steps(gap_analysis: Dict) -> List[str]:
    """
    Generate actionable next steps based on skill gaps with corrected logic.
    
    Uses comparable values:
    - total_required: count of all required skills
    - match_pct: percentage (0-100) of proficient skills
    """
    steps = []
    
    missing_count = len(gap_analysis["missing"])
    improvement_count = len(gap_analysis["needs_improvement"])
    proficient_count = len(gap_analysis["proficient"])
    
    # Calculate total and percentage
    total_required = proficient_count + improvement_count + missing_count
    match_pct = gap_analysis.get("match_percentage", 0)
    
    # Rule 1: Missing foundation skills
    if missing_count > 0:
        top_missing = gap_analysis["missing"][:3]
        skills_str = ", ".join([s["skill"] for s in top_missing])
        steps.append(f"Learn the missing foundation skills: {skills_str}")
    
    # Rule 2: Skills needing improvement
    if improvement_count > 0:
        top_improve = gap_analysis["needs_improvement"][:3]
        skills_str = ", ".join([s["skill"] for s in top_improve])
        steps.append(f"Strengthen partially matched skills through quizzes, labs, and mini projects: {skills_str}")
    
    # Rule 3: Portfolio and CV when 60%+ proficient (using correct comparison)
    if proficient_count >= max(1, int(total_required * 0.6)):
        steps.append("Build or refine a portfolio project that proves these skills")
        steps.append("Update your CV and LinkedIn with validated skills")
    
    # Rule 4: Interview prep when highly matched
    if match_pct >= 80:
        steps.append("Start applying for similar roles")
        steps.append("Prepare for interviews based on the required skills")
    
    # Rule 5: Fallback if no steps generated
    if not steps:
        steps.append("Continue building your skill profile")
    
    return steps


def clear_cache():
    """Clear all cached data and models."""
    global _job_features_cache, _ml_model_cache, _feature_columns_cache
    _job_features_cache = None
    _ml_model_cache = None
    _feature_columns_cache = None
    logger.info("All caches cleared")
