"""
Advanced Recommendation System API Client

Wrapper for Advanced-Recommendation backend endpoints.
Handles role profiles, skill gaps, course recommendations, and GNN-based analysis.

BASE_URL: http://localhost:8001 (default)
"""
import json
import logging
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8001"


class SkillDeficit:
    """Represents a skill deficit for course recommendation."""
    
    def __init__(
        self,
        skill_name: str,
        deficit: float,
        importance: float,
        confidence: float = 0.0,
        match_strength: float = 0.0,
    ):
        self.skill_name = skill_name
        self.deficit = deficit
        self.importance = importance
        self.confidence = confidence
        self.match_strength = match_strength
    
    def dict(self):
        return {
            "skill_name": self.skill_name,
            "deficit": self.deficit,
            "importance": self.importance,
            "confidence": self.confidence,
            "match_strength": self.match_strength,
        }


class RecommendationClient:
    """Client for Advanced Recommendation System backend."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """
        List all available roles with job counts.
        
        Returns:
            List of roles with basic information
        """
        url = f"{self.base_url}/roles"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def role_skill_profile(self, role_key: str, top_n: int = 100) -> Dict[str, Any]:
        """
        Get TF-IDF skill importance profile for a role.
        
        Args:
            role_key: Role identifier (e.g., 'ai_ml_engineer')
            top_n: Number of top skills to return (default: 100)
        
        Returns:
            RoleSkillProfile with importance scores
        """
        url = f"{self.base_url}/roles/{role_key}/skill-profile"
        params = {"top_n": top_n}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def role_category_profile(
        self,
        role_key: str,
        top_skills: int = 5
    ) -> Dict[str, Any]:
        """
        Get aggregated category profile for a role.
        
        Computes category-level importance by aggregating TF-IDF scores
        for all skills within each category.
        
        Args:
            role_key: Role identifier
            top_skills: Number of top skills per category (default: 5)
        
        Returns:
            RoleCategoryProfileResponse with categories and skills
        """
        url = f"{self.base_url}/roles/{role_key}/category-profile"
        params = {"top_skills": top_skills}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def skill_confidence(
        self,
        candidate_id: str,
        top_n: int = 100
    ) -> Dict[str, Any]:
        """
        Get evidence-weighted skill confidence for a candidate.
        
        Args:
            candidate_id: Candidate identifier
            top_n: Number of top skills to return (default: 100)
        
        Returns:
            CandidateSkillProfile with confidence scores
        """
        url = f"{self.base_url}/candidates/{candidate_id}/skill-confidence"
        params = {"top_n": top_n}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    
    def skill_gap(
        self,
        candidate_id: str,
        role_key: str,
        top_k: int = 25
    ) -> Dict[str, Any]:
        """
        Perform advanced skill gap analysis with deficit ranking.
        
        Includes category-aware gaps and graded skill matching.
        
        Args:
            candidate_id: Candidate identifier
            role_key: Target role identifier
            top_k: Number of top deficits to return (default: 25)
        
        Returns:
            SkillGapResponseEnhanced with ranked deficits and categories
        """
        url = f"{self.base_url}/candidates/{candidate_id}/roles/{role_key}/skill-gap-advanced"
        params = {"top_k": top_k}
        logger.info(f"Analyzing gap for {candidate_id} → {role_key} (top {top_k})")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    
    def recommend_courses(
        self,
        candidate_id: str,
        role_key: str,
        top_k: int = 25,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Recommend courses optimized for deficit reduction.
        
        Includes category coverage gains for each course.
        
        Args:
            candidate_id: Candidate identifier
            role_key: Target role identifier
            top_k: Number of top deficits to consider (default: 25)
            top_n: Number of courses to recommend (default: 10)
        
        Returns:
            CourseRecommendationResponseEnhanced with recommendations
        """
        url = f"{self.base_url}/candidates/{candidate_id}/roles/{role_key}/recommendations"
        params = {"top_k": top_k, "top_n": top_n}
        logger.info(f"Recommending courses for {candidate_id} → {role_key}")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    
    def recommend_for_job_gap(
        self,
        candidate_id: str,
        deficits: List[SkillDeficit],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Recommend courses for job gap analysis (no role required).
        
        Useful for custom job descriptions where you have computed
        skill deficits but don't have a predefined role_key.
        
        Args:
            candidate_id: Candidate identifier
            deficits: List of SkillDeficit objects
            top_n: Number of courses to recommend (default: 10)
        
        Returns:
            CourseRecommendationResponse with recommendations
        """
        url = f"{self.base_url}/candidates/{candidate_id}/courses/recommend-for-job-gap"
        params = {"top_n": top_n}
        
        # Convert deficits to dicts
        deficit_dicts = [d.dict() if hasattr(d, 'dict') else d for d in deficits]
        
        logger.info(f"Recommending courses for job gap: {candidate_id} ({len(deficits)} deficits)")
        r = requests.post(url, params=params, json=deficit_dicts, timeout=30)
        r.raise_for_status()
        return r.json()
    
    def project_relevance(
        self,
        candidate_id: str,
        role_key: str,
        top_n: int = 5,
        top_k_role: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze how relevant a candidate's projects are to a target role.
        
        Args:
            candidate_id: Candidate identifier
            role_key: Target role identifier
            top_n: Number of top projects to return (default: 5)
            top_k_role: Number of top role skills to consider (default: 100)
        
        Returns:
            ProjectRelevanceResponse with scored projects
        """
        url = f"{self.base_url}/candidates/{candidate_id}/roles/{role_key}/project-relevance"
        params = {"top_n": top_n, "top_k_role": top_k_role}
        logger.info(f"Analyzing project relevance for {candidate_id} → {role_key}")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    
    def missing_skills_gnn(
        self,
        candidate_id: str,
        role_key: str,
        top_k: int = 20,
        explain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        **GNN-Based Missing Skill Ranking** (Link Prediction).
        
        Combines Graph Neural Network predictions with skill confidence
        and role importance using the formula:
        
            final_score = (1 - P_has) * importance * P_gnn
        
        Args:
            candidate_id: Candidate identifier
            role_key: Target role identifier
            top_k: Number of top missing skills to return (default: 20)
            explain: Add SHAP explanations ('formula', 'feature', or 'graph')
        
        Returns:
            GNNMissingSkillsResponse with ranked missing skills
        """
        url = f"{self.base_url}/candidates/{candidate_id}/roles/{role_key}/missing-skills-gnn"
        params = {"top_k": top_k}
        if explain:
            params["explain"] = explain
        logger.info(f"Computing GNN missing skills for {candidate_id} → {role_key}")
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        return r.json()
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cached data (admin endpoint)."""
        url = f"{self.base_url}/cache/clear"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()


def main():
    """Demo: Exercise Advanced Recommendation endpoints."""
    client = RecommendationClient()
    
    print("=" * 70)
    print("Advanced Recommendation System Client Demo")
    print("=" * 70)
    
    # List roles
    try:
        print("\n📋 Fetching available roles...")
        roles = client.list_roles()
        print(f"✓ Found {len(roles)} roles")
        if roles:
            for role in roles[:3]:
                print(f"  - {role.get('name')} ({role.get('role_key')}): {role.get('job_count')} jobs")
    except Exception as e:
        print(f"✗ Failed to list roles: {e}")
        return
    
    # Get role profile
    try:
        print("\n📊 Fetching AI/ML Engineer skill profile...")
        profile = client.role_skill_profile("ai_ml_engineer", top_n=10)
        print(f"✓ Role: {profile.get('role_name')}")
        print(f"  Total jobs: {profile.get('total_jobs')}")
        print(f"  Top 3 skills:")
        for skill in profile.get('skills', [])[:3]:
            print(f"    - {skill.get('skill_name')}: {skill.get('importance'):.4f}")
    except Exception as e:
        print(f"✗ Failed to get role profile: {e}")
    
    # Get candidate skill confidence
    candidate_id = "CAND_TEST_001"
    try:
        print(f"\n👤 Fetching skill confidence for {candidate_id}...")
        confidence = client.skill_confidence(candidate_id, top_n=10)
        skills = confidence.get('skills', [])
        print(f"✓ Found {len(skills)} skills")
        if skills:
            for skill in skills[:3]:
                print(f"  - {skill.get('skill_name')}: {skill.get('confidence'):.2f}")
    except Exception as e:
        print(f"✗ Failed to get skill confidence: {e}")
    
    # Skill gap analysis
    try:
        print(f"\n🔍 Analyzing skill gap: {candidate_id} → ai_ml_engineer...")
        gap = client.skill_gap(candidate_id, "ai_ml_engineer", top_k=10)
        deficits = gap.get('deficits', [])
        print(f"✓ Found {len(deficits)} skill deficits")
        if deficits:
            for deficit in deficits[:3]:
                print(f"  - {deficit.get('skill_name')}: deficit={deficit.get('deficit'):.2f}, importance={deficit.get('importance'):.4f}")
    except Exception as e:
        print(f"✗ Failed to analyze gap: {e}")
    
    # Course recommendations
    try:
        print(f"\n📚 Recommending courses...")
        courses = client.recommend_courses(candidate_id, "ai_ml_engineer", top_k=10, top_n=5)
        recs = courses.get('recommendations', [])
        print(f"✓ Recommended {len(recs)} courses")
        if recs:
            for course in recs[:2]:
                print(f"  - {course.get('course_name')}: gain={course.get('gain_score'):.2f}")
    except Exception as e:
        print(f"✗ Failed to recommend courses: {e}")
    
    # Project relevance
    try:
        print(f"\n🎯 Analyzing project relevance...")
        projects = client.project_relevance(candidate_id, "ai_ml_engineer", top_n=5)
        proj_list = projects.get('projects', [])
        score = projects.get('candidate_project_score')
        print(f"✓ Overall project score: {score:.2f}")
        print(f"  Top projects: {len(proj_list)}")
        if proj_list:
            for proj in proj_list[:2]:
                print(f"    - {proj.get('project_name')}: relevance={proj.get('relevance_score'):.2f}")
    except Exception as e:
        print(f"✗ Failed to analyze project relevance: {e}")
    
    print("\n" + "=" * 70)
    print("Demo complete. Use RecommendationClient in your code.")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
