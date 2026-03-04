"""
API routes for Advanced Recommendation System.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from database import Neo4jConnection
from services import (
    SkillConfidenceService,
    RoleImportanceService,
    DeficitService,
    CourseRecommendationService,
    ProjectRelevanceService,
    CategoryService,
)
from services.gnn_ranking_service import GNNRankingService
from models import (
    RoleBasic,
    RoleSkillProfile,
    SkillImportance,
    CandidateSkillProfile,
    SkillConfidence,
    SkillGapResponse,
    SkillDeficit,
    CourseRecommendationResponse,
    CourseRecommendation,
    ProjectRelevanceResponse,
    ProjectRelevance,
    # NEW: Category-aware models
    RoleCategoryProfileResponse,
    RoleCategoryProfile,
    CategorySkillImportance,
    SkillGapResponseEnhanced,
    SkillDeficitEnhanced,
    CourseRecommendationResponseEnhanced,
    CourseRecommendationEnhanced,
    # NEW: GNN-based models
    GNNMissingSkillsResponse,
)
from utils import cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", tags=["Info"])
def root():
    """API information and health check."""
    return {
        "service": "Advanced Skill Gap & Course Recommendation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "roles": "/roles",
            "role_profile": "/roles/{role_key}/skill-profile",
            "role_category_profile": "/roles/{role_key}/category-profile",
            "candidate_confidence": "/candidates/{candidate_id}/skill-confidence",
            "skill_gap": "/candidates/{candidate_id}/roles/{role_key}/skill-gap-advanced",
            "recommendations": "/candidates/{candidate_id}/roles/{role_key}/recommendations",
            "project_relevance": "/candidates/{candidate_id}/roles/{role_key}/project-relevance",
            "gnn_missing_skills": "/candidates/{candidate_id}/roles/{role_key}/missing-skills-gnn",
        }
    }


@router.get("/roles", response_model=list[RoleBasic], tags=["Roles"])
def list_roles():
    """
    List all available roles with job counts.
    
    Returns:
        List of roles with basic information
    """
    logger.info("Fetching all roles")
    
    with Neo4jConnection.get_session() as session:
        query = """
        MATCH (r:Role)
        OPTIONAL MATCH (r)<-[:BELONGS_TO_ROLE]-(j:Job)
        WITH r, count(DISTINCT j) AS job_count
        RETURN r.role_key AS role_key, r.name AS name, job_count
        ORDER BY job_count DESC
        """
        result = session.run(query)
        
        roles = [
            RoleBasic(
                role_key=record["role_key"],
                name=record["name"],
                job_count=record["job_count"]
            )
            for record in result
        ]
    
    logger.info(f"Found {len(roles)} roles")
    return roles


@router.get(
    "/roles/{role_key}/skill-profile",
    response_model=RoleSkillProfile,
    tags=["Roles"]
)
def get_role_skill_profile(
    role_key: str,
    top_n: int = Query(100, ge=1, le=500, description="Number of top skills to return")
):
    """
    Get TF-IDF skill importance profile for a role.
    
    Args:
        role_key: Role identifier
        top_n: Number of top skills to return (default: 100)
        
    Returns:
        Complete skill profile with TF-IDF scores
    """
    logger.info(f"Fetching skill profile for role: {role_key}")
    
    with Neo4jConnection.get_session() as session:
        # Compute role importance (cached)
        skill_importance, total_jobs, role_name = RoleImportanceService.compute_role_importance(
            session, role_key
        )
        
        if not skill_importance:
            raise HTTPException(status_code=404, detail=f"Role not found: {role_key}")
        
        # Get total roles for response
        query_total = "MATCH (r:Role) RETURN count(DISTINCT r) AS total_roles"
        total_roles = session.run(query_total).single()["total_roles"]
        
        # Sort by importance and take top-N
        sorted_skills = sorted(
            skill_importance.items(),
            key=lambda x: x[1]["importance"],
            reverse=True
        )[:top_n]
        
        skills = [
            SkillImportance(
                skill_name=skill_name,
                tf=data["tf"],
                df=data["df"],
                idf=data["idf"],
                importance=data["importance"],
                percentage=data["percentage"]
            )
            for skill_name, data in sorted_skills
        ]
    
    return RoleSkillProfile(
        role_key=role_key,
        role_name=role_name,
        total_jobs=total_jobs,
        total_roles=total_roles,
        skills=skills
    )


@router.get(
    "/roles/{role_key}/category-profile",
    response_model=RoleCategoryProfileResponse,
    tags=["Roles"]
)
def get_role_category_profile(
    role_key: str,
    top_skills: int = Query(5, ge=1, le=20, description="Top skills per category")
):
    """
    Get aggregated category profile for a role (NEW).
    
    Computes category-level importance by aggregating TF-IDF scores
    for all skills within each category.
    
    Args:
        role_key: Role identifier
        top_skills: Number of top skills to show per category (default: 5)
        
    Returns:
        Category profile with importance sums and top skills
    """
    logger.info(f"Fetching category profile for role: {role_key}")
    
    with Neo4jConnection.get_session() as session:
        # Compute role importance (cached)
        skill_importance, total_jobs, role_name = RoleImportanceService.compute_role_importance(
            session, role_key
        )
        
        if not skill_importance:
            raise HTTPException(status_code=404, detail=f"Role not found: {role_key}")
        
        # Compute category profile
        category_profiles, category_coverage = CategoryService.compute_role_category_profile(
            session, role_key, skill_importance, top_skills
        )
        
        # Convert to response model
        categories = [
            RoleCategoryProfile(
                category=cp["category"],
                importance_sum=cp["importance_sum"],
                num_role_skills=cp["num_role_skills"],
                top_skills=[
                    CategorySkillImportance(**skill)
                    for skill in cp["top_skills"]
                ]
            )
            for cp in category_profiles
        ]
    
    return RoleCategoryProfileResponse(
        role_key=role_key,
        role_name=role_name,
        total_jobs=total_jobs,
        categories=categories,
        category_coverage=category_coverage
    )


@router.get(
    "/candidates/{candidate_id}/skill-confidence",
    response_model=CandidateSkillProfile,
    tags=["Candidates"]
)
def get_candidate_skill_confidence(
    candidate_id: str,
    top_n: int = Query(100, ge=1, le=500, description="Number of top skills to return")
):
    """
    Get evidence-weighted skill confidence for a candidate.
    
    Args:
        candidate_id: Candidate identifier
        top_n: Number of top skills to return (default: 100)
        
    Returns:
        Skill confidence profile with evidence sources
    """
    logger.info(f"Fetching skill confidence for candidate: {candidate_id}")
    
    try:
        with Neo4jConnection.get_session() as session:
            skill_confidence = SkillConfidenceService.compute_confidence(session, candidate_id)
            
            if not skill_confidence:
                raise HTTPException(
                    status_code=404,
                    detail=f"Candidate not found or has no skill evidence: {candidate_id}"
                )
            
            # Sort by confidence and take top-N
            sorted_skills = sorted(
                skill_confidence.items(),
                key=lambda x: x[1]["confidence"],
                reverse=True
            )[:top_n]
            
            skills = [
                SkillConfidence(
                    skill_name=skill_name,
                    confidence=data["confidence"],
                    evidence_sources=data["evidence_sources"],
                    evidence_count=data["evidence_count"]
                )
                for skill_name, data in sorted_skills
            ]
        
        return CandidateSkillProfile(
            candidate_id=candidate_id,
            skills=skills
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get skill confidence: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve skill confidence: {str(e)}"
        )


@router.get(
    "/candidates/{candidate_id}/roles/{role_key}/skill-gap-advanced",
    response_model=SkillGapResponseEnhanced,
    tags=["Skill Gap Analysis"]
)
def analyze_skill_gap(
    candidate_id: str,
    role_key: str,
    top_k: int = Query(25, ge=1, le=100, description="Number of top deficits to return")
):
    """
    Perform advanced skill gap analysis with deficit ranking and category grouping (ENHANCED).
    
    NEW: Now includes category-aware gaps and skill category mappings.
    
    Args:
        candidate_id: Candidate identifier
        role_key: Target role identifier
        top_k: Number of top deficits to return (default: 25)
        
    Returns:
        Ranked skill deficits with TF-IDF importance + category gaps
    """
    logger.info(f"Analyzing skill gap: candidate={candidate_id}, role={role_key}")
    
    with Neo4jConnection.get_session() as session:
        # Compute candidate confidence
        candidate_confidence = SkillConfidenceService.compute_confidence(session, candidate_id)
        
        # Compute role importance
        role_importance, total_jobs, role_name = RoleImportanceService.compute_role_importance(
            session, role_key
        )
        
        if not role_importance:
            raise HTTPException(status_code=404, detail=f"Role not found: {role_key}")
        
        # Compute deficits with GRADED matching
        deficits = DeficitService.compute_deficits_with_graded_matching(
            session, candidate_id, role_importance, top_k
        )
        
        # Get total roles
        query_total = "MATCH (r:Role) RETURN count(DISTINCT r) AS total_roles"
        total_roles = session.run(query_total).single()["total_roles"]
        
        # NEW: Get skill categories for deficits
        deficit_skills = [d["skill_name"] for d in deficits]
        skill_to_category = CategoryService.get_skill_categories_batch(session, deficit_skills)
        
        # NEW: Build P_has map for category gap computation
        P_has_map = {}
        for skill_name in role_importance.keys():
            # Check if candidate has this skill
            if skill_name in candidate_confidence:
                P_has_map[skill_name] = candidate_confidence[skill_name]["confidence"]
            else:
                # Check for graded match (from deficits)
                deficit_entry = next(
                    (d for d in deficits if d["skill_name"] == skill_name),
                    None
                )
                if deficit_entry:
                    P_has_map[skill_name] = deficit_entry["match_strength"]
                else:
                    P_has_map[skill_name] = 0.0
        
        # NEW: Aggregate category gaps
        category_gaps, mapping_stats = CategoryService.aggregate_category_gaps(
            session,
            candidate_id,
            role_key,
            deficits,
            P_has_map,
            role_importance
        )
        
        # Convert to response model with categories
        deficits_response = []
        for d in deficits:
            category = skill_to_category.get(d["skill_name"])
            deficits_response.append(SkillDeficitEnhanced(
                skill_name=d["skill_name"],
                p_has=d["match_strength"],
                tf=d["tf"],
                df=d["df"],
                idf=d["idf"],
                importance=d["importance"],
                deficit=d["deficit"],
                category=category  # NEW: Optional field
            ))
        
        return SkillGapResponseEnhanced(
            candidate_id=candidate_id,
            role_key=role_key,
            role_name=role_name,
            total_jobs=total_jobs,
            total_roles=total_roles,
            deficits=deficits_response,
            category_gaps=category_gaps,  # NEW
            category_mapping_stats=mapping_stats  # NEW
        )


@router.get(
    "/candidates/{candidate_id}/roles/{role_key}/recommendations",
    response_model=CourseRecommendationResponseEnhanced,
    tags=["Course Recommendations"]
)
def recommend_courses(
    candidate_id: str,
    role_key: str,
    top_k: int = Query(25, ge=1, le=100, description="Number of deficits to consider"),
    top_n: int = Query(10, ge=1, le=50, description="Number of courses to recommend")
):
    """
    Recommend courses optimized for deficit reduction with category awareness (ENHANCED).
    
    NEW: Now includes category coverage gains for each course.
    
    Args:
        candidate_id: Candidate identifier
        role_key: Target role identifier
        top_k: Number of top deficits to consider (default: 25)
        top_n: Number of courses to recommend (default: 10)
        
    Returns:
        Top-N course recommendations with gain scores + category improvements
    """
    logger.info(f"Recommending courses: candidate={candidate_id}, role={role_key}")
    
    try:
        with Neo4jConnection.get_session() as session:
            # Compute candidate confidence
            candidate_confidence = SkillConfidenceService.compute_confidence(session, candidate_id)
            
            # Check if candidate exists
            if not candidate_confidence:
                raise HTTPException(
                    status_code=404,
                    detail=f"Candidate not found or has no skills: {candidate_id}"
                )
            
            # Compute role importance
            role_importance, total_jobs, role_name = RoleImportanceService.compute_role_importance(
                session, role_key
            )
            
            if not role_importance:
                raise HTTPException(status_code=404, detail=f"Role not found: {role_key}")
            
            # Compute top-K deficits with GRADED matching
            top_deficits = DeficitService.compute_deficits_with_graded_matching(
                session, candidate_id, role_importance, top_k
            )
            
            # Build P_has map for category gains
            P_has_map = {}
            for skill_name in role_importance.keys():
                if skill_name in candidate_confidence:
                    P_has_map[skill_name] = candidate_confidence[skill_name]["confidence"]
                else:
                    deficit_entry = next(
                        (d for d in top_deficits if d["skill_name"] == skill_name),
                        None
                    )
                    if deficit_entry:
                        P_has_map[skill_name] = deficit_entry["match_strength"]
                    else:
                        P_has_map[skill_name] = 0.0
            
            # Recommend courses
            recommendations = CourseRecommendationService.recommend_courses(
                session, candidate_id, top_deficits, top_n
            )
            
            # NEW: Compute category gains for each course
            enhanced_recommendations = []
            for rec in recommendations:
                # Compute category gains
                category_gains = CategoryService.compute_category_gains(
                    session,
                    rec["covered_deficit_skills"],
                    role_importance,
                    P_has_map
                )
                
                enhanced_recommendations.append(
                    CourseRecommendationEnhanced(
                        **rec,
                        category_gain=category_gains if category_gains else None  # NEW
                    )
                )
            
            return CourseRecommendationResponseEnhanced(
                candidate_id=candidate_id,
                role_key=role_key,
                role_name=role_name,
                top_k_deficits_considered=len(top_deficits),
                recommendations=enhanced_recommendations
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recommend courses: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate course recommendations: {str(e)}"
        )


@router.get(
    "/candidates/{candidate_id}/roles/{role_key}/project-relevance",
    response_model=ProjectRelevanceResponse,
    tags=["Project Analysis"]
)
def analyze_project_relevance(
    candidate_id: str,
    role_key: str,
    top_n: int = Query(5, ge=1, le=20, description="Number of top projects to return"),
    top_k_role: int = Query(100, ge=10, le=500, description="Number of top role skills to consider")
):
    """
    Analyze how relevant a candidate's projects are to a target role.
    
    **Algorithm:**
    1. Get top-K role skills with TF-IDF importance scores
    2. For each project, compute:
       - Exact skill matches: full importance
       - Similar skills (via SIMILAR_TO): importance × similarity
       - Relevance = sum(matched_importance) / sum(total_role_importance)
    3. Sort projects by relevance (descending)
    4. Calculate candidate_project_score:
       - Average of top 3 projects (or max if fewer than 3)
    
    **Args:**
    - `candidate_id`: Candidate identifier
    - `role_key`: Target role identifier
    - `top_n`: Number of top relevant projects to return (default: 5)
    - `top_k_role`: Number of top role skills to consider (default: 100)
    
    **Returns:**
    Project relevance analysis with:
    - Sorted projects by relevance score
    - Matched skills for each project
    - Overall candidate project score
    
    **Example Response:**
    ```json
    {
      "candidate_id": "CAND_001",
      "role_key": "ai_ml_engineer",
      "role_name": "AI/ML Engineer",
      "projects": [
        {
          "project_name": "AI Chatbot System",
          "relevance_score": 0.75,
          "matched_role_skills": ["Python", "TensorFlow", "NLP", "FastAPI"],
          "project_skills": ["Python", "TensorFlow", "NLP", "FastAPI", "Docker"],
          "num_matched": 4,
          "num_project_skills": 5
        }
      ],
      "candidate_project_score": 0.68,
      "total_projects": 12
    }
    ```
    
    **Use Cases:**
    - Evaluate project portfolio alignment with role
    - Identify most relevant past work
    - Assess practical experience in role-specific technologies
    - Weight project experience in hiring decisions
    """
    logger.info(f"Analyzing project relevance: candidate={candidate_id}, role={role_key}")
    
    try:
        with Neo4jConnection.get_session() as session:
            result = ProjectRelevanceService.compute_project_relevance(
                session, candidate_id, role_key, top_n, top_k_role
            )
        
        if result.get("error"):
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        
        return ProjectRelevanceResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze project relevance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/cache/clear", tags=["Admin"])
def clear_cache():
    """
    Clear all cached data (admin endpoint).
    
    Returns:
        Cache clear confirmation
    """
    logger.info("Clearing cache")
    cache.clear()
    return {"status": "success", "message": "Cache cleared"}


@router.get(
    "/candidates/{candidate_id}/roles/{role_key}/missing-skills-gnn",
    response_model=GNNMissingSkillsResponse,
    tags=["GNN Recommendations"]
)
def get_missing_skills_gnn(
    candidate_id: str,
    role_key: str,
    top_k: int = Query(20, ge=1, le=100, description="Number of top missing skills to return"),
    explain: Optional[str] = Query(None, pattern="^(formula|feature|graph)$", 
                                    description="Add SHAP explanations: formula, feature, or graph")
):
    """
    **GNN-Based Missing Skill Ranking** (Research-Grade Link Prediction)
    
    Combines Graph Neural Network predictions with skill confidence and role importance
    to rank missing skills using the formula:
    
        final_score = (1 - P_has) * importance * P_gnn
    
    Where:
    - **P_has**: Current skill confidence from evidence aggregation (0-1)
    - **P_gnn**: GNN predicted probability for acquiring skill (0-1)
    - **importance**: TF-IDF role importance score
    - **gap_magnitude**: 1 - P_has (how much skill is missing)
    
    **Features:**
    - Graph Neural Network trained on 51K+ person-skill edges
    - Heterogeneous graph with persons, skills, projects, and categories
    - Inference optimized for <200ms per candidate
    - Category-level aggregation for explainability
    - Optional SHAP explanations for interpretability
    
    **SHAP Explanation Levels:**
    - **formula**: How P_gnn, importance, gap contribute to final_score (fastest)
    - **feature**: Which candidate skills/projects influenced P_gnn (medium)
    - **graph**: Which graph neighbors contributed to prediction (slowest, most detailed)
    
    **Use Cases:**
    - Personalized learning path recommendations
    - Skill gap analysis with learning potential
    - Role readiness assessment
    
    Args:
        candidate_id: Candidate identifier
        role_key: Role identifier
        top_k: Number of top missing skills to return (1-100, default: 20)
        explain: Optional SHAP explanation level: "formula", "feature", or "graph"
        
    Returns:
        GNNMissingSkillsResponse with ranked skills and category summary
        
    Raises:
        404: Candidate or role not found
        500: GNN model not loaded or inference error
    """
    logger.info(f"GNN missing skills request: candidate={candidate_id}, role={role_key}, top_k={top_k}, explain={explain}")
    
    try:
        with Neo4jConnection.get_session() as session:
            # Rank missing skills using GNN
            ranked_skills, category_summary, metadata = GNNRankingService.rank_missing_skills_for_role(
                session=session,
                candidate_id=candidate_id,
                role_key=role_key,
                top_k=top_k,
                p_has_threshold=0.6
            )
            
            # Add SHAP explanations if requested
            if explain:
                from services.shap_explainer_service import shap_explainer
                ranked_skills = shap_explainer.explain_top_recommendations(
                    session=session,
                    ranked_skills=ranked_skills,
                    candidate_id=candidate_id,
                    explanation_level=explain
                )
            
            # Build response
            response = GNNMissingSkillsResponse(
                candidate_id=candidate_id,
                role_key=role_key,
                role_name=metadata['role_name'],
                top_missing_skills=ranked_skills,
                category_summary=category_summary,
                metadata=metadata
            )
            
            logger.info(f"GNN ranking completed: {len(ranked_skills)} skills, {len(category_summary)} categories, explain={explain}")
            return response
    
    except ValueError as e:
        # Candidate not found in graph or role not found
        logger.error(f"Not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except RuntimeError as e:
        # GNN model not loaded
        logger.error(f"GNN service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to rank missing skills with GNN: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

