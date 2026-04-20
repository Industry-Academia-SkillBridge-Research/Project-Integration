"""
Job Recommendation Service

Recommends jobs to students based on their skill scores
and job skill requirements from the job feature matrix.

Updated for flat skill structure.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ..models.skill import SkillProfileClaimed
import logging

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
JOB_FEATURES_FILE = DATA_DIR / "job_parent_skill_features.csv"

# Cache for job features dataframe
_job_features_cache = None


def load_jobs_feature_table() -> pd.DataFrame:
    """
    Load job parent skill features from CSV.
    
    Returns:
        DataFrame with columns: job_id, title, company, role_key, + parent skill columns
        
    Raises:
        FileNotFoundError: If job_parent_skill_features.csv not found
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
    
    # Cache for future use
    _job_features_cache = df
    
    logger.info(f"Loaded {len(df):,} jobs with {len(df.columns)} columns")
    return df


def get_student_parent_skill_scores(db: Session, student_id: str) -> Dict[str, float]:
    """
    Get student's skill scores from claimed skills table (flat structure).
    
    Args:
        db: Database session
        student_id: Student identifier
        
    Returns:
        Dictionary mapping skill_name -> score (0-100)
    """
    # Get claimed skills
    claimed_skills = db.query(SkillProfileClaimed).filter(
        SkillProfileClaimed.student_id == student_id
    ).all()
    
    if claimed_skills:
        logger.info(f"Using {len(claimed_skills)} claimed skills for {student_id}")
        return {
            skill.skill_name: skill.claimed_score
            for skill in claimed_skills
        }
    
    logger.warning(f"No skills found for student {student_id}")
    return {}


def recommend_jobs_for_student(
    db: Session,
    student_id: str,
    top_k: int = 10,
    threshold: float = 70.0,
    role_key: Optional[str] = None
) -> List[Dict]:
    """
    Recommend jobs for a student based on their parent skill scores.
    
    Args:
        db: Database session
        student_id: Student identifier
        top_k: Number of top jobs to return
        threshold: Minimum score to consider a skill "matched" (default 70)
        role_key: Optional filter by role_key (e.g., 'AIML', 'FULLSTACK')
        
    Returns:
        List of job recommendations with match analysis
        
    Raises:
        FileNotFoundError: If job features file not found
        ValueError: If no student skills found
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
    
    # Get student scores
    student_scores = get_student_parent_skill_scores(db, student_id)
    
    if not student_scores:
        raise ValueError(f"No parent skills found for student {student_id}")
    
    # Identify parent skill columns (exclude metadata columns)
    metadata_cols = ['job_id', 'title', 'company', 'role_key', 'seniority_level']
    parent_skill_cols = [col for col in jobs_df.columns if col not in metadata_cols]
    
    logger.info(f"Analyzing {len(jobs_df)} jobs against {len(student_scores)} student skills")
    
    # Analyze each job
    recommendations = []
    
    for idx, job_row in jobs_df.iterrows():
        # Get required skills for this job (where feature = 1)
        required_skills = [
            skill for skill in parent_skill_cols
            if job_row[skill] == 1
        ]
        
        if not required_skills:
            # Skip jobs with no mapped skills
            continue
        
        # Calculate match metrics
        skill_scores = []
        matched_skills = []
        missing_skills = []
        
        for skill in required_skills:
            student_score = student_scores.get(skill, 0.0)
            skill_scores.append(student_score)
            
            if student_score >= threshold:
                matched_skills.append({
                    "skill": skill,
                    "score": round(student_score, 1)
                })
            else:
                gap = threshold - student_score
                missing_skills.append({
                    "skill": skill,
                    "score": round(student_score, 1),
                    "gap": round(gap, 1)
                })
        
        # Calculate overall match score
        match_score = sum(skill_scores) / len(skill_scores) if skill_scores else 0.0
        
        # Top contributors (skills with highest student scores)
        top_contributors = sorted(
            [{"skill": s, "score": round(student_scores.get(s, 0.0), 1)} 
             for s in required_skills],
            key=lambda x: x["score"],
            reverse=True
        )[:5]
        
        recommendations.append({
            "job_id": job_row['job_id'],
            "title": job_row['title'],
            "company": job_row['company'],
            "role_key": job_row['role_key'],
            "description": job_row.get('description', ''),
            "match_score": round(match_score, 1),
            "total_required_skills": len(required_skills),
            "matched_skills_count": len(matched_skills),
            "missing_skills_count": len(missing_skills),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "top_contributors": top_contributors
        })
    
    # Sort by match score descending
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    logger.info(
        f"Generated {len(recommendations)} recommendations for {student_id}, "
        f"returning top {top_k}"
    )
    
    return recommendations[:top_k]


def clear_cache():
    """Clear the cached job features dataframe. Useful for testing."""
    global _job_features_cache
    _job_features_cache = None
    logger.info("Job features cache cleared")
