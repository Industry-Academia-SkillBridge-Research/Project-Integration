"""
Agent Runtime API Client

Wrapper for Agent-Runtime backend endpoints.
Handles CV data submission, PDF upload, and explainability requests.

BASE_URL: http://localhost:8002 (default)
"""
import json
import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8002"


class AgentRuntimeClient:
    """Client for Agent-Runtime backend."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def health(self) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            Health status with Neo4j and Recommendation API connectivity
        """
        url = f"{self.base_url}/health"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    
    def run_agent(
        self,
        cv_data: Dict[str, Any],
        role_key: str,
        top_k: int = 25,
        include_xai: bool = True,
        ranking_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete agentic pipeline (Extract → Normalize → Write → Analyze).
        
        Args:
            cv_data: CV data in ExtractedData format with fields:
                - candidate_id (required)
                - candidate_name (required)
                - current_role (optional)
                - experience_months (optional)
                - all_skills (list of skill names)
                - projects_and_technologies_involved (optional)
                See schemas_new.py ExtractedData model for full schema
            role_key: Target role key (e.g., 'ai_ml_engineer', 'data_scientist')
            top_k: Number of top skill deficits to return (default: 25)
            include_xai: Include explainability analysis (default: True)
            ranking_method: Override ranking method ('symbolic', 'hybrid', 'additive_gnn')
        
        Returns:
            AgentRunResponse with pipeline results
        """
        url = f"{self.base_url}/agent/run"
        params = {
            "role_key": role_key,
            "top_k": top_k,
            "include_xai": include_xai,
        }
        if ranking_method:
            params["ranking_method"] = ranking_method
        
        logger.info(f"Submitting CV for role {role_key} with ranking={ranking_method or 'default'}")
        r = requests.post(url, params=params, json=cv_data, timeout=120)
        r.raise_for_status()
        return r.json()
    
    def run_agent_from_pdf(
        self,
        pdf_path: str,
        role_key: str,
        top_k: int = 25,
        include_xai: bool = True,
        ranking_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run agentic pipeline from uploaded PDF/DOCX resume.
        
        Supports:
        - PDF (native or scanned with OCR fallback)
        - DOCX files
        
        Uses LLM parsing:
        - Primary: Open Router Llama 3.1 70B (free)
        - Fallback: Gemini Flash (free)
        
        Args:
            pdf_path: Path to PDF or DOCX file
            role_key: Target role key
            top_k: Number of top deficits to return
            include_xai: Include XAI analysis
            ranking_method: Override ranking method
        
        Returns:
            AgentRunResponse with pipeline results
        """
        url = f"{self.base_url}/agent/run-from-pdf"
        params = {
            "role_key": role_key,
            "top_k": top_k,
            "include_xai": include_xai,
        }
        if ranking_method:
            params["ranking_method"] = ranking_method
        
        logger.info(f"Uploading PDF {pdf_path} for role {role_key}")
        with open(pdf_path, "rb") as f:
            files = {"cv_file": (pdf_path, f, "application/pdf")}
            r = requests.post(url, params=params, files=files, timeout=180)
        
        r.raise_for_status()
        return r.json()
    
    def skill_explain(
        self,
        candidate_id: str,
        role_key: str,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Skill-level explainability: Show contribution of each skill deficit.
        
        Args:
            candidate_id: Candidate ID
            role_key: Target role key
            top_n: Number of top contributors to return (default: 10)
        
        Returns:
            SkillExplainResponse with contributions and percentages
        """
        url = f"{self.base_url}/runtime/skill-explain"
        params = {
            "candidate_id": candidate_id,
            "role_key": role_key,
            "top_n": top_n,
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    
    def predict_explain(
        self,
        candidate_id: str,
        role_key: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        User-friendly model-level explainability (SHAP-based).
        
        Returns SHAP feature impacts converted into actionable sentences.
        
        Args:
            candidate_id: Candidate ID
            role_key: Target role key
            top_k: Number of top factors to return (default: 5)
        
        Returns:
            FriendlyPredictExplainResponse with SHAP explanations
        """
        url = f"{self.base_url}/runtime/predict-explain"
        params = {
            "candidate_id": candidate_id,
            "role_key": role_key,
            "top_k": top_k,
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()


def main():
    """Demo: Exercise Agent-Runtime endpoints."""
    client = AgentRuntimeClient()
    
    print("=" * 60)
    print("Agent-Runtime Client Demo")
    print("=" * 60)
    
    # Health check
    try:
        health = client.health()
        print(f"\n✓ Health: {health}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return
    
    # Example: Run agent with sample CV (using correct schema)
    sample_cv = {
        "candidate_id": "TEST_001",
        "candidate_name": "John Doe",
        "current_role": "Software Engineer",
        "experience_months": 24,
        "all_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "projects_and_technologies_involved": [
            {
                "project_name": "ML Pipeline",
                "project_description": "Built automated data pipeline",
                "technologies_used": ["Python", "Pandas", "Scikit-learn", "PostgreSQL"],
            }
        ],
    }
    
    try:
        print("\n📤 Running agent for AI/ML Engineer role...")
        result = client.run_agent(
            cv_data=sample_cv,
            role_key="ai_ml_engineer",
            top_k=10,
            include_xai=True,
        )
        print(f"✓ Agent completed. Status: {result.get('status', 'unknown')}")
        print(f"  Readiness: {result.get('readiness_score', 'N/A')}")
        print(f"  Top deficits: {len(result.get('skill_gap_top', []))} skills")
        if result.get('xai'):
            print(f"  XAI included: Yes")
    except Exception as e:
        print(f"✗ Agent run failed: {e}")
    
    print("\n" + "=" * 60)
    print("Demo complete. Use AgentRuntimeClient in your code.")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
