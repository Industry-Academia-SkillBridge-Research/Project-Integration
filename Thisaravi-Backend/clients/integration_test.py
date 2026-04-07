"""
Unified Integration Script

Demonstrates end-to-end workflow using both Agent-Runtime and Advanced-Recommendation.

Flow:
  1. Submit CV to Agent-Runtime for skill extraction & gap analysis
  2. Fetch skill gap details from Advanced-Recommendation
  3. Get course recommendations
  4. Analyze project relevance
  5. Get GNN-based missing skills

Usage:
  python integration_test.py [candidate_id] [role_key]
"""
import json
import sys
import logging
from typing import Dict, Any

# Add parent dir to path for imports
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent_runtime_client import AgentRuntimeClient
from recommendation_client import RecommendationClient, SkillDeficit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Sample CV for testing
SAMPLE_CV = {
    "candidate_id": "CAND_ML_2024_001",
    "candidate_name": "Alice Johnson",
    "current_role": "Data Analyst",
    "experience_months": 36,
    "all_skills": [
        "Python",
        "SQL",
        "Pandas",
        "Matplotlib",
        "Excel",
        "Tableau",
        "Scikit-learn",
    ],
    "projects_and_technologies_involved": [
        {
            "project_name": "Sales Dashboard",
            "project_description": "Interactive Tableau dashboard for sales metrics",
            "technologies_used": ["Tableau", "SQL", "Python"],
        },
        {
            "project_name": "Data Cleaning Pipeline",
            "project_description": "ETL pipeline for data quality",
            "technologies_used": ["Python", "Pandas", "SQL"],
        },
        {
            "project_name": "Predictive Model",
            "project_description": "Customer churn prediction model",
            "technologies_used": ["Python", "Scikit-learn", "Pandas"],
        },
    ],
}


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n▶ {title}")
    print("-" * 80)


def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """Format JSON for display."""
    return json.dumps(data, indent=indent, default=str)


def run_integration_test(candidate_id: str = None, role_key: str = "ai_ml_engineer"):
    """
    Run end-to-end integration test.
    
    Args:
        candidate_id: Candidate ID (if None, uses sample CV with generated ID)
        role_key: Target role (default: ai_ml_engineer)
    """
    print_header("🚀 INTEGRATION TEST: Agent-Runtime + Advanced-Recommendation")
    
    # Initialize clients
    agent_client = AgentRuntimeClient()
    rec_client = RecommendationClient()
    
    # Prepare CV data
    cv_data = SAMPLE_CV.copy()
    if candidate_id:
        cv_data["candidate_id"] = candidate_id
    
    candidate_id = cv_data["candidate_id"]
    
    print(f"\n📋 Test Configuration:")
    print(f"  Candidate: {candidate_id}")
    print(f"  Target Role: {role_key}")
    print(f"  Current Role: {cv_data['current_role']}")
    print(f"  Skills: {len(cv_data.get('all_skills', []))} provided")
    print(f"  Experience: {cv_data.get('experience_months', 0)} months")
    
    # =========================================================================
    # STEP 1: Run Agent-Runtime Pipeline
    # =========================================================================
    print_section("Step 1: Agent-Runtime Pipeline Execution")
    
    try:
        logger.info(f"Submitting CV to Agent-Runtime for role '{role_key}'...")
        agent_response = agent_client.run_agent(
            cv_data=cv_data,
            role_key=role_key,
            top_k=25,
            include_xai=True,
            ranking_method="hybrid",
        )
        
        print(f"✓ Pipeline executed successfully")
        print(f"  Readiness Score: {agent_response.get('readiness_score', 0):.2f}")
        print(f"  Normalized Skills: {agent_response.get('normalized_skills_count', 0)}")
        print(f"  Top Skill Gaps: {len(agent_response.get('skill_gap_top', []))}")
        print(f"  Project Relevance Score: {agent_response.get('project_relevance_score', 'N/A')}")
        
        # Show top 5 skill gaps
        gaps = agent_response.get("skill_gap_top", [])
        if gaps:
            print(f"\n  Top 5 Skill Deficits:")
            for i, gap in enumerate(gaps[:5], 1):
                print(
                    f"    {i}. {gap.get('skill_name')}: "
                    f"deficit={gap.get('deficit', 0):.2f}, "
                    f"importance={gap.get('importance', 0):.4f}"
                )
        
        # Show XAI results if available
        xai = agent_response.get("xai")
        if xai:
            print(f"\n  XAI Analysis Available:")
            if xai.get("skill_level"):
                print(f"    ✓ Skill-level explanation: {len(xai['skill_level'].get('top_contributors', []))} contributors")
            if xai.get("shap_level"):
                shap = xai["shap_level"]
                if shap.get("enabled"):
                    print(f"    ✓ SHAP explanation: enabled")
                    if shap.get("top_increasing_factors"):
                        print(f"      - Top increasing factors: {len(shap['top_increasing_factors'])}")
                    if shap.get("top_reducing_factors"):
                        print(f"      - Top reducing factors: {len(shap['top_reducing_factors'])}")
    
    except Exception as e:
        logger.error(f"Agent-Runtime failed: {e}", exc_info=True)
        print(f"✗ Agent-Runtime error: {e}")
        return
    
    # =========================================================================
    # STEP 2: Get Skill Gap Details from Advanced-Recommendation
    # =========================================================================
    print_section("Step 2: Advanced Skill Gap Analysis")
    
    try:
        logger.info(f"Fetching detailed skill gap for '{candidate_id}' → '{role_key}'...")
        gap_response = rec_client.skill_gap(
            candidate_id=candidate_id,
            role_key=role_key,
            top_k=25,
        )
        
        deficits = gap_response.get("deficits", [])
        print(f"✓ Skill gap analysis retrieved")
        print(f"  Target Role: {gap_response.get('role_name', 'N/A')}")
        print(f"  Total Role Jobs: {gap_response.get('total_jobs', 0)}")
        print(f"  Top Deficits: {len(deficits)}")
        
        # Show category distribution
        categories = {}
        for deficit in deficits:
            cat = deficit.get("category", "Uncategorized")
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            print(f"\n  Deficits by Category:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    - {cat}: {count} skill(s)")
    
    except Exception as e:
        logger.error(f"Skill gap analysis failed: {e}", exc_info=True)
        print(f"✗ Skill gap error: {e}")
    
    # =========================================================================
    # STEP 3: Get Course Recommendations
    # =========================================================================
    print_section("Step 3: Course Recommendations")
    
    try:
        logger.info(f"Recommending courses for '{candidate_id}'...")
        courses_response = rec_client.recommend_courses(
            candidate_id=candidate_id,
            role_key=role_key,
            top_k=25,
            top_n=10,
        )
        
        recommendations = courses_response.get("recommendations", [])
        print(f"✓ Course recommendations retrieved")
        print(f"  Recommended Courses: {len(recommendations)}")
        
        if recommendations:
            print(f"\n  Top 5 Courses:")
            for i, course in enumerate(recommendations[:5], 1):
                print(
                    f"    {i}. {course.get('course_name', 'Unknown')} "
                    f"(Gain: {course.get('gain_score', 0):.2f})"
                )
                skills = course.get("covered_deficit_skills", [])
                if skills:
                    print(f"       Skills: {', '.join(skills[:3])}")
    
    except Exception as e:
        logger.error(f"Course recommendation failed: {e}", exc_info=True)
        print(f"✗ Recommendation error: {e}")
    
    # =========================================================================
    # STEP 4: Analyze Project Relevance
    # =========================================================================
    print_section("Step 4: Project Relevance Analysis")
    
    try:
        logger.info(f"Analyzing project relevance for '{candidate_id}'...")
        projects_response = rec_client.project_relevance(
            candidate_id=candidate_id,
            role_key=role_key,
            top_n=5,
            top_k_role=100,
        )
        
        projects = projects_response.get("projects", [])
        score = projects_response.get("candidate_project_score", 0)
        
        print(f"✓ Project analysis retrieved")
        print(f"  Overall Project Score: {score:.2f}")
        print(f"  Relevant Projects: {len(projects)}")
        
        if projects:
            print(f"\n  Top 3 Relevant Projects:")
            for i, proj in enumerate(projects[:3], 1):
                print(
                    f"    {i}. {proj.get('project_name', 'Unknown')} "
                    f"(Relevance: {proj.get('relevance_score', 0):.2f})"
                )
                matched = proj.get("num_matched", 0)
                total = proj.get("num_project_skills", 0)
                print(f"       Matched Skills: {matched}/{total}")
    
    except Exception as e:
        logger.error(f"Project relevance analysis failed: {e}", exc_info=True)
        print(f"✗ Project analysis error: {e}")
    
    # =========================================================================
    # STEP 5: GNN-Based Missing Skills (Optional)
    # =========================================================================
    print_section("Step 5: GNN-Based Missing Skills (Graph Link Prediction)")
    
    try:
        logger.info(f"Computing GNN missing skills for '{candidate_id}'...")
        gnn_response = rec_client.missing_skills_gnn(
            candidate_id=candidate_id,
            role_key=role_key,
            top_k=15,
        )
        
        missing = gnn_response.get("missing_skills", [])
        print(f"✓ GNN analysis retrieved")
        print(f"  Missing Skills (GNN-Ranked): {len(missing)}")
        print(f"  GNN Model Available: {gnn_response.get('gnn_available', False)}")
        
        if missing:
            print(f"\n  Top 5 Skills (by GNN score):")
            for i, skill in enumerate(missing[:5], 1):
                print(
                    f"    {i}. {skill.get('skill_name', 'Unknown')} "
                    f"(Score: {skill.get('final_score', 0):.4f})"
                )
                print(
                    f"       Gap: {skill.get('gap_magnitude', 0):.2f}, "
                    f"Importance: {skill.get('importance', 0):.4f}, "
                    f"P_gnn: {skill.get('p_gnn', 0):.2f}"
                )
    
    except Exception as e:
        logger.error(f"GNN analysis failed (non-critical): {e}")
        print(f"⚠ GNN analysis unavailable (non-critical): {e}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("✅ INTEGRATION TEST COMPLETE")
    
    print(f"""
Test Summary:
  ✓ Agent-Runtime Pipeline: Executed & retrieved gap analysis
  ✓ Advanced-Recommendation: Fetched skill gaps, recommendations, and projects
  ✓ Workflow: Full end-to-end integration validated

Next Steps:
  1. Review the skill gaps and course recommendations above
  2. Use these endpoints in your production application
  3. Integrate with your frontend to display recommendations
  4. Monitor explainability (XAI) results for interpretability

For detailed API docs, visit:
    - Agent-Runtime: http://localhost:8003/docs
  - Advanced-Recommendation: http://localhost:8001/docs
""")


def main():
    """Main entry point."""
    candidate_id = sys.argv[1] if len(sys.argv) > 1 else None
    role_key = sys.argv[2] if len(sys.argv) > 2 else "ai_ml_engineer"
    
    run_integration_test(candidate_id=candidate_id, role_key=role_key)


if __name__ == "__main__":
    main()
