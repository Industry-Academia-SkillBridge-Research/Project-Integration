"""
Job Skill Scoring Service

Computes job skill scores by aggregating child skill scores through
the childskill_to_jobskill_map.csv mapping.

This layer provides canonical, short job-skill tags (SQL, Python, Git, etc.)
derived from detailed child skills, making it easier to match against
job requirements.
"""

import logging
from typing import Dict, List, Tuple
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
JOB_SKILLS_FILE = DATA_DIR / "job_skills.csv"
MAPPING_FILE = DATA_DIR / "childskill_to_jobskill_map.csv"

# Cache for static data
_job_skills_cache = None
_mapping_cache = None


def load_job_skills() -> pd.DataFrame:
    """
    Load job skills master list from CSV.
    
    Returns:
        DataFrame with columns: JobSkillID, JobSkillName, Category, Aliases
    """
    global _job_skills_cache
    
    if _job_skills_cache is not None:
        return _job_skills_cache
    
    if not JOB_SKILLS_FILE.exists():
        raise FileNotFoundError(
            f"Job skills file not found: {JOB_SKILLS_FILE}\n"
            f"Run: python scripts/build_job_skill_maps.py"
        )
    
    logger.info(f"Loading job skills from {JOB_SKILLS_FILE}")
    df = pd.read_csv(JOB_SKILLS_FILE)
    _job_skills_cache = df
    
    logger.info(f"Loaded {len(df)} job skills across {df['Category'].nunique()} categories")
    return df


def load_child_to_job_mapping() -> pd.DataFrame:
    """
    Load child skill → job skill mapping from CSV.
    
    Returns:
        DataFrame with columns: ChildSkill, JobSkillID, MapWeight, Notes
    """
    global _mapping_cache
    
    if _mapping_cache is not None:
        return _mapping_cache
    
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(
            f"Mapping file not found: {MAPPING_FILE}\n"
            f"Run: python scripts/build_job_skill_maps.py"
        )
    
    logger.info(f"Loading child-to-job mapping from {MAPPING_FILE}")
    df = pd.read_csv(MAPPING_FILE)
    _mapping_cache = df
    
    logger.info(
        f"Loaded {len(df)} mappings: "
        f"{df['ChildSkill'].nunique()} child skills → "
        f"{df['JobSkillID'].nunique()} job skills"
    )
    return df


def compute_job_skill_scores(
    child_skill_scores: Dict[str, float],
    db: Session = None
) -> Dict:
    """
    Compute job skill scores by aggregating child skill scores.
    
    Algorithm:
    1. For each job skill, find all child skills that map to it
    2. Aggregate: raw_score = Σ(child_score × map_weight)
    3. Normalize to 0-100 scale
    
    Args:
        child_skill_scores: Dict mapping child_skill_name → claimed_score (0-100)
        db: Database session (optional, for future extensions)
        
    Returns:
        Dictionary with:
        - job_skill_scores: Dict[str, float] - JobSkillID → score
        - job_skill_details: List[Dict] - Full details for each job skill
        - mapping_stats: Dict - Statistics about the mapping
    """
    logger.info(f"Computing job skill scores from {len(child_skill_scores)} child skills")
    
    # Load static data
    try:
        job_skills_df = load_job_skills()
        mapping_df = load_child_to_job_mapping()
    except FileNotFoundError as e:
        logger.error(f"Missing required data files: {e}")
        return {
            "job_skill_scores": {},
            "job_skill_details": [],
            "mapping_stats": {"error": str(e)}
        }
    
    # Build job skill aggregations
    job_skill_data = {}
    
    for _, row in mapping_df.iterrows():
        child_skill = row['ChildSkill']
        job_skill_id = row['JobSkillID']
        map_weight = row['MapWeight']
        
        # Get child skill score (default 0 if not found)
        child_score = child_skill_scores.get(child_skill, 0.0)
        
        # Initialize job skill entry
        if job_skill_id not in job_skill_data:
            job_skill_data[job_skill_id] = {
                'total_weighted_score': 0.0,
                'total_weight': 0.0,
                'contributing_skills': []
            }
        
        # Aggregate
        contribution = child_score * map_weight
        job_skill_data[job_skill_id]['total_weighted_score'] += contribution
        job_skill_data[job_skill_id]['total_weight'] += map_weight
        
        if child_score > 0:  # Only track non-zero contributors
            job_skill_data[job_skill_id]['contributing_skills'].append({
                'child_skill': child_skill,
                'score': child_score,
                'weight': map_weight,
                'contribution': contribution
            })
    
    # Compute final scores and build output
    job_skill_scores = {}
    job_skill_details = []
    
    for job_skill_id, data in job_skill_data.items():
        # Get job skill metadata
        job_info = job_skills_df[job_skills_df['JobSkillID'] == job_skill_id].iloc[0]
        
        # Compute normalized score
        if data['total_weight'] > 0:
            # Weighted average, already in 0-100 scale
            job_score = data['total_weighted_score'] / data['total_weight']
        else:
            job_score = 0.0
        
        # Ensure score is in valid range
        job_score = max(0.0, min(100.0, job_score))
        
        # Store by ID
        job_skill_scores[job_skill_id] = job_score
        
        # Build detailed entry
        job_skill_details.append({
            'job_skill_id': job_skill_id,
            'job_skill_name': job_info['JobSkillName'],
            'category': job_info['Category'],
            'score': round(job_score, 2),
            'contributing_child_skills': len(data['contributing_skills']),
            'total_weight': round(data['total_weight'], 2),
            # Optional: include top contributors
            'top_contributors': sorted(
                data['contributing_skills'],
                key=lambda x: x['contribution'],
                reverse=True
            )[:3]  # Top 3
        })
    
    # Sort by score descending
    job_skill_details.sort(key=lambda x: x['score'], reverse=True)
    
    # Mapping statistics
    mapping_stats = {
        'total_child_skills': len(child_skill_scores),
        'mapped_child_skills': len(set(mapping_df['ChildSkill'])),
        'total_job_skills_defined': len(job_skills_df),
        'job_skills_with_scores': len(job_skill_scores),
        'unmapped_child_skills': len(set(child_skill_scores.keys()) - set(mapping_df['ChildSkill']))
    }
    
    logger.info(
        f"Computed {len(job_skill_scores)} job skill scores from "
        f"{mapping_stats['mapped_child_skills']} mapped child skills"
    )
    
    return {
        'job_skill_scores': job_skill_scores,
        'job_skill_details': job_skill_details,
        'mapping_stats': mapping_stats
    }


def get_job_skill_by_name(job_skill_name: str) -> str:
    """
    Get JobSkillID from JobSkillName.
    
    Args:
        job_skill_name: Name of the job skill
        
    Returns:
        JobSkillID or None if not found
    """
    job_skills_df = load_job_skills()
    match = job_skills_df[job_skills_df['JobSkillName'] == job_skill_name]
    
    if len(match) > 0:
        return match.iloc[0]['JobSkillID']
    return None


def get_job_skills_for_child_skill(child_skill: str) -> List[Tuple[str, float]]:
    """
    Get all job skills that a child skill maps to.
    
    Args:
        child_skill: Name of the child skill
        
    Returns:
        List of (JobSkillID, MapWeight) tuples
    """
    mapping_df = load_child_to_job_mapping()
    matches = mapping_df[mapping_df['ChildSkill'] == child_skill]
    
    return [(row['JobSkillID'], row['MapWeight']) for _, row in matches.iterrows()]


def get_child_skills_for_job_skill(job_skill_id: str) -> List[Tuple[str, float]]:
    """
    Get all child skills that contribute to a job skill.
    
    Args:
        job_skill_id: JobSkillID
        
    Returns:
        List of (ChildSkill, MapWeight) tuples
    """
    mapping_df = load_child_to_job_mapping()
    matches = mapping_df[mapping_df['JobSkillID'] == job_skill_id]
    
    return [(row['ChildSkill'], row['MapWeight']) for _, row in matches.iterrows()]


def compute_job_skill_scores_for_student(student_id: str, db: Session) -> Dict:
    """
    Convenience wrapper to compute job skill scores for a student.
    
    Fetches child skill scores from database and computes job skill scores.
    
    Args:
        student_id: Student identifier
        db: Database session
        
    Returns:
        Dictionary with job_skill_scores, job_skill_details, and mapping_stats
    """
    from ..models.skill import SkillProfileClaimed
    
    # Fetch child skill scores
    child_skills = db.query(SkillProfileClaimed).filter(
        SkillProfileClaimed.student_id == student_id
    ).all()
    
    # Build dict: skill_name → claimed_score
    child_skill_scores = {
        skill.skill_name: skill.claimed_score
        for skill in child_skills
    }
    
    # Compute job skill scores
    return compute_job_skill_scores(child_skill_scores, db)
