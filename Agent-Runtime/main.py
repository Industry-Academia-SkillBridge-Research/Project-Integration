"""
Agent Runtime Backend - FastAPI Application

Agentic orchestration for CV processing and skill gap analysis:
    Extractor → Normalizer → KG Writer → Gap Analyzer

NEW: Job Description image/PDF → Gap Analysis pipeline

Run with:
    uvicorn main:app --reload --port 8003
    
Swagger docs:
    http://localhost:8003/docs
"""
import logging
from contextlib import asynccontextmanager
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from config import (
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    CORS_ORIGINS,
    LOG_LEVEL,
    LOG_FORMAT,
    RECOMMENDATION_API_BASE_URL,
    SKILL_GAP_RANKING_METHOD,
)
from database import Neo4jConnection
from agents import ExtractorAgent, NormalizerAgent, KGWriterTool, GapAnalyzerTool
from models import (
    ExtractedData,
    AgentRunRequest,
    AgentRunResponse,
    HealthResponse,
    SkillConfidenceResult,
    SkillDeficitResult,
)
from models.xai_schemas import (
    SkillExplainResponse,
    PredictExplainResponse,
    FriendlyPredictExplainResponse,
    XAIResponse,
    SkillContribution,
)
from services.xai_service import get_xai_service
from services.cv_parser_service import get_cv_parser_service

# Import job gap router
from routes.job_gap_routes import router as job_gap_router
from routes.job_skill_test_routes import router as job_skill_test_router

# Try to import explainer routes (optional - requires PyTorch)
try:
    from routes.explainer_routes import router as explainer_router
    EXPLAINER_AVAILABLE = True
    print("[OK] Explainer routes imported successfully")
except ImportError as e:
    print(f"[WARN] AI Explainer routes not available (missing PyTorch): {e}")
    explainer_router = None
    EXPLAINER_AVAILABLE = False
except Exception as e:
    print(f"[WARN] AI Explainer routes failed to load: {type(e).__name__}: {e}")
    explainer_router = None
    EXPLAINER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info("[START] Starting Agent Runtime Backend...")
    try:
        Neo4jConnection.get_driver()
        logger.info("[OK] Application startup complete")
    except Exception as e:
        logger.error(f"[ERROR] Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("[STOP] Shutting down...")
    Neo4jConnection.close()
    logger.info("[OK] Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
extractor = ExtractorAgent()
normalizer = NormalizerAgent()
# Use configured ranking method (symbolic, hybrid, or additive_gnn)
gap_analyzer = GapAnalyzerTool(ranking_method=SKILL_GAP_RANKING_METHOD)

# Initialize XAI service
xai_service = get_xai_service()

# Include routers
app.include_router(job_gap_router)
app.include_router(job_skill_test_router)

# Include explainer router only if available
if EXPLAINER_AVAILABLE and explainer_router:
    app.include_router(explainer_router)
    logger.info("[OK] AI Explainer routes enabled")
    print(f"[OK] AI Explainer routes registered: {len(explainer_router.routes)} routes")
else:
    logger.warning("[WARN] AI Explainer routes disabled (PyTorch not available)")
    print("[WARN] AI Explainer routes disabled")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Info"])
def root():
    """API information and available endpoints."""
    return {
        "service": "Agent Runtime Backend",
        "version": API_VERSION,
        "status": "running",
        "description": "Agentic orchestration for CV processing and skill gap analysis",
        "architecture": "Extractor → Normalizer → KG Writer → Gap Analyzer",
        "endpoints": {
            "run_agent": "POST /agent/run",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
def health_check():
    """
    Health check endpoint.
    
    Checks:
    - Neo4j connection
    - Recommendation API availability (optional)
    
    Returns:
        Health status
    """
    logger.info("Health check requested")
    
    # Check Neo4j
    neo4j_connected = False
    try:
        driver = Neo4jConnection.get_driver()
        driver.verify_connectivity()
        neo4j_connected = True
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
    
    # Check Recommendation API (optional)
    recommendation_api_available = gap_analyzer.check_api_health()
    
    status = "healthy" if neo4j_connected else "degraded"
    
    return HealthResponse(
        status=status,
        neo4j_connected=neo4j_connected,
        recommendation_api_available=recommendation_api_available
    )


@app.get("/runtime/skill-explain", response_model=SkillExplainResponse, tags=["Explainability"])
def skill_explain(
    candidate_id: str = Query(..., description="Candidate ID"),
    role_key: str = Query(..., description="Target role key"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top contributors to return")
):
    """
    Skill-level explainability: Show contribution of each skill deficit.
    
    Computes contribution_percent = deficit / sum(deficits) for each skill.
    
    Args:
        candidate_id: Candidate ID
        role_key: Target role key
        top_n: Number of top contributors
        
    Returns:
        Skill contributions with percentages
    """
    logger.info(f"Skill explain: candidate={candidate_id}, role={role_key}")
    
    try:
        # Call gap analysis API to get deficits
        gap_result = gap_analyzer.analyze_gap(
            candidate_id=candidate_id,
            role_key=role_key,
            top_k=50  # Get more for analysis
        )
        
        deficits = gap_result.get("skill_gap_top", [])
        
        if not deficits:
            return SkillExplainResponse(
                candidate_id=candidate_id,
                role_key=role_key,
                top_contributors=[],
                total_deficit=0.0
            )
        
        # Convert to dict format
        deficits_dict = [
            {
                "skill_name": d.skill_name,
                "deficit": d.deficit,
                "importance": d.importance,
                "p_has": d.match_strength
            }
            for d in deficits
        ]
        
        # Compute contributions
        contributions = xai_service.compute_skill_level_explanation(
            deficits_dict,
            top_n=top_n
        )
        
        total_deficit = sum(d["deficit"] for d in deficits_dict)
        
        return SkillExplainResponse(
            candidate_id=candidate_id,
            role_key=role_key,
            top_contributors=[
                SkillContribution(**c) for c in contributions
            ],
            total_deficit=round(total_deficit, 4)
        )
        
    except Exception as e:
        logger.error(f"Skill explain failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Skill explainability failed: {str(e)}"
        )


@app.get("/runtime/predict-explain", response_model=FriendlyPredictExplainResponse, tags=["Explainability"])
def predict_explain(
    candidate_id: str = Query(..., description="Candidate ID"),
    role_key: str = Query(..., description="Target role key"),
    top_k: int = Query(5, ge=1, le=10, description="Number of top features to return")
):
    """
    User-friendly model-level explainability with plain English explanations.
    
    Returns SHAP feature impacts converted into simple, actionable sentences
    that explain why the skill gap is high or low.
    
    Args:
        candidate_id: Candidate ID
        role_key: Target role key
        top_k: Number of top positive/negative contributors (default 5)
        
    Returns:
        Friendly SHAP explanation with human-readable messages
    """
    logger.info(f"Predict explain (friendly): candidate={candidate_id}, role={role_key}")
    
    try:
        # Build feature row from Neo4j
        with Neo4jConnection.get_session() as session:
            feature_row = xai_service.build_feature_row(
                session,
                candidate_id,
                role_key
            )
        
        if feature_row is None:
            return FriendlyPredictExplainResponse(
                enabled=False,
                reason="Failed to build feature row from Neo4j"
            )
        
        # Compute SHAP explanation (now returns friendly format)
        explanation = xai_service.compute_shap_explanation(
            feature_row,
            top_k=top_k
        )
        
        # Add candidate/role info
        if explanation.get("enabled"):
            explanation["candidate_id"] = candidate_id
            explanation["role_key"] = role_key
        
        return FriendlyPredictExplainResponse(**explanation)
        
    except Exception as e:
        logger.error(f"Predict explain failed: {e}", exc_info=True)
        return FriendlyPredictExplainResponse(
            enabled=False,
            reason=f"Error: {str(e)}"
        )


@app.get("/runtime/predict-explain-legacy", response_model=PredictExplainResponse, tags=["Explainability"])
def predict_explain_legacy(
    candidate_id: str = Query(..., description="Candidate ID"),
    role_key: str = Query(..., description="Target role key"),
    top_k: int = Query(10, ge=1, le=20, description="Number of top features to return")
):
    """
    Legacy model-level explainability endpoint (backward compatibility).
    
    Use /runtime/predict-explain instead for user-friendly explanations.
    
    Args:
        candidate_id: Candidate ID
        role_key: Target role key
        top_k: Number of top positive/negative contributors
        
    Returns:
        SHAP explanation with feature impacts (legacy format)
    """
    logger.info(f"Predict explain (legacy): candidate={candidate_id}, role={role_key}")
    
    try:
        # Build feature row from Neo4j
        with Neo4jConnection.get_session() as session:
            feature_row = xai_service.build_feature_row(
                session,
                candidate_id,
                role_key
            )
        
        if feature_row is None:
            return PredictExplainResponse(
                enabled=False,
                reason="Failed to build feature row from Neo4j"
            )
        
        # Compute SHAP explanation
        explanation = xai_service.compute_shap_explanation(
            feature_row,
            top_k=top_k
        )
        
        # Add candidate/role info
        if explanation.get("enabled"):
            explanation["candidate_id"] = candidate_id
            explanation["role_key"] = role_key
            
            # Convert friendly format back to legacy format
            if "top_increasing_factors" in explanation:
                explanation["top_positive_contributors"] = [
                    {
                        "feature": item["feature"],
                        "feature_key": item.get("feature", ""),
                        "impact": item["impact"],
                        "description": item["message"],
                        "interpretation": item["message"]
                    }
                    for item in explanation["top_increasing_factors"]
                ]
                explanation["top_negative_contributors"] = [
                    {
                        "feature": item["feature"],
                        "feature_key": item.get("feature", ""),
                        "impact": item["impact"],
                        "description": item["message"],
                        "interpretation": item["message"]
                    }
                    for item in explanation["top_reducing_factors"]
                ]
                explanation["skill_gap_prediction"] = explanation.get("predicted_skill_gap_index")
                explanation["readiness_prediction"] = explanation.get("predicted_readiness")
        
        return PredictExplainResponse(**explanation)
        
    except Exception as e:
        logger.error(f"Predict explain (legacy) failed: {e}", exc_info=True)
        return PredictExplainResponse(
            enabled=False,
            reason=f"Error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Predict explain failed: {e}", exc_info=True)
        return PredictExplainResponse(
            enabled=False,
            reason=f"Prediction explainability failed: {str(e)}"
        )


@app.post("/agent/run", response_model=AgentRunResponse, tags=["Agent"])
def run_agent(
    cv_data: ExtractedData,
    role_key: str = Query(..., description="Target role key for gap analysis (e.g., 'ai_ml_engineer')"),
    top_k: int = Query(25, ge=1, le=100, description="Number of top skill deficits to return"),
    include_xai: bool = Query(True, description="Include explainability analysis (skill-level + SHAP)"),
    ranking_method: str = Query(
        None,
        description="Ranking method: 'symbolic' (TF-IDF), 'hybrid' (GNN × importance × gap), or 'additive_gnn'. Default: from config (currently 'hybrid')"
    )
):
    """
    Run complete agentic pipeline: Extract → Normalize → Write → Analyze.
    
    **Pipeline:**
    
    1. **Extractor Agent**: Validates incoming JSON
    2. **Normalizer Agent**: Maps skills to canonical names (Python3 → Python)
    3. **KG Writer Tool**: Creates/updates candidate graph in Neo4j
    4. **Gap Analyzer Tool**: Runs skill confidence & gap analysis with configurable ranking
    
    **NEW: Configurable Ranking Methods:**
    - **symbolic** (Traditional): deficit = (1 - P_has) × importance  
      Fast, interpretable, based on TF-IDF importance
      
    - **hybrid** (GNN-Powered): final_score = gap × importance_norm × P_gnn  
      **DEFAULT** - Personalized using trained Graph Neural Network  
      Prioritizes learnable high-impact skills based on candidate's graph context
      
    - **additive_gnn** (Experimental): 0.3×(1-P_has) + 0.4×importance + 0.3×P_gnn  
      Weighted sum approach, less aggressive filtering
    
    **Request Body:**
    Accepts CV data in combined_resumes.json format (see sample_extracted_cv_1.json)
    
    **Query Parameters:**
    - role_key: Target role (e.g., "ai_ml_engineer", "data_scientist")
    - top_k: Number of top skill deficits to return (default: 25)
    - include_xai: Include explainability analysis (default: true)
    - ranking_method: Override default ranking method (optional)
    
    **Response:**
    Returns combined results including:
    - Normalization statistics
    - Neo4j write statistics
    - Top skills by confidence
    - Top skill deficits (ranked by selected method)
    - Readiness score
    - XAI explanations (if include_xai=true)
    
    Args:
        cv_data: CV data from combined_resumes.json format
        role_key: Target role key for gap analysis
        top_k: Number of top deficits to return
        include_xai: Whether to include XAI analysis
        ranking_method: Override default ranking method (optional)
        
    Returns:
        AgentRunResponse with complete pipeline results
    """
    logger.info(
        f"🤖 Agent pipeline started: candidate={cv_data.candidate_id}, "
        f"role={role_key}, ranking={ranking_method or SKILL_GAP_RANKING_METHOD}"
    )
    
    candidate_id = cv_data.candidate_id
    
    try:
        # DEBUG: Log incoming data type and structure
        logger.info(f"DEBUG: cv_data type = {type(cv_data)}")
        logger.info(f"DEBUG: cv_data has skills attr? {hasattr(cv_data, 'skills')}")
        if hasattr(cv_data, 'skills'):
            logger.info(f"DEBUG: skills type = {type(cv_data.skills)}, len = {len(cv_data.skills) if cv_data.skills else 0}")
        
        # ====================================================================
        # Step 1: Extractor Agent - Validate JSON
        # ====================================================================
        logger.info("Step 1/4: Extractor Agent")
        validated_data = extractor.extract(cv_data)
        
        # ====================================================================
        # Step 2: Normalizer Agent - Canonicalize skills
        # ====================================================================
        logger.info("Step 2/4: Normalizer Agent")
        normalized_data = normalizer.normalize_extracted_data(validated_data)
        
        # Count normalized skills
        normalized_skills_count = len(normalized_data.all_skills) if normalized_data.all_skills else 0
        
        # ====================================================================
        # Step 3: KG Writer Tool - Write to Neo4j
        # ====================================================================
        logger.info("Step 3/4: KG Writer Tool")
        with Neo4jConnection.get_session() as session:
            write_result = KGWriterTool.write_candidate(session, normalized_data)
        
        if not write_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to write to Neo4j: {write_result.message}"
            )
        
        # ====================================================================
        # Step 4: Gap Analyzer Tool - Run analysis
        # ====================================================================
        logger.info("Step 4/4: Gap Analyzer Tool")
        
        # Use request-specific ranking method if provided, otherwise use configured default
        effective_ranking_method = ranking_method or SKILL_GAP_RANKING_METHOD
        
        # Create analyzer with specified method
        request_gap_analyzer = GapAnalyzerTool(ranking_method=effective_ranking_method)
        
        gap_result = request_gap_analyzer.analyze_gap(
            candidate_id=candidate_id,
            role_key=role_key,
            top_k=top_k
        )
        
        logger.info(f"Gap analysis complete using '{effective_ranking_method}' method")
        
        # ====================================================================
        # Build Response
        # ====================================================================
        
        # ====================================================================
        # Step 5: XAI (Optional)
        # ====================================================================
        xai_result = None
        if include_xai:
            logger.info("Step 5/5: Computing XAI")
            try:
                # Skill-level explanation
                deficits_dict = [
                    {
                        "skill_name": d.skill_name,
                        "deficit": d.deficit,
                        "importance": d.importance,
                        "p_has": d.match_strength
                    }
                    for d in gap_result.get("skill_gap_top", [])
                ]
                
                skill_contributions = xai_service.compute_skill_level_explanation(
                    deficits_dict,
                    top_n=10
                )
                
                total_deficit = sum(d["deficit"] for d in deficits_dict)
                
                skill_level_xai = SkillExplainResponse(
                    candidate_id=candidate_id,
                    role_key=role_key,
                    top_contributors=[
                        SkillContribution(**c) for c in skill_contributions
                    ],
                    total_deficit=round(total_deficit, 4)
                )
                
                # SHAP-level explanation
                with Neo4jConnection.get_session() as session:
                    feature_row = xai_service.build_feature_row(
                        session,
                        candidate_id,
                        role_key
                    )
                
                if feature_row is not None:
                    shap_explanation = xai_service.compute_shap_explanation(
                        feature_row,
                        top_k=5  # Changed to 5 for user-friendly display
                    )
                    
                    logger.info(f"SHAP explanation enabled: {shap_explanation.get('enabled')}")
                    logger.info(f"SHAP top_reducing_factors count: {len(shap_explanation.get('top_reducing_factors', []))}")
                    logger.info(f"SHAP top_increasing_factors count: {len(shap_explanation.get('top_increasing_factors', []))}")
                    
                    if shap_explanation.get("enabled"):
                        shap_explanation["candidate_id"] = candidate_id
                        shap_explanation["role_key"] = role_key
                    
                    shap_level_xai = FriendlyPredictExplainResponse(**shap_explanation)
                else:
                    shap_level_xai = FriendlyPredictExplainResponse(
                        enabled=False,
                        reason="Failed to build feature row"
                    )
                
                xai_result = XAIResponse(
                    skill_level=skill_level_xai,
                    shap_level=shap_level_xai
                )
                
                logger.info("✓ XAI computed successfully")
                
            except Exception as xai_error:
                logger.warning(f"XAI computation failed (non-fatal): {xai_error}")
                xai_result = None
        
        # ====================================================================
        # Step 6: Fetch Project Relevance (Optional)
        # ====================================================================
        project_relevance_score = None
        relevant_projects = None
        
        try:
            logger.info("Fetching project relevance...")
            project_url = f"{RECOMMENDATION_API_BASE_URL}/candidates/{candidate_id}/roles/{role_key}/project-relevance"
            project_response = requests.get(project_url, params={"top_n": 5, "top_k": 25}, timeout=5)
            
            if project_response.status_code == 200:
                project_data = project_response.json()
                project_relevance_score = project_data.get("candidate_project_score")
                relevant_projects = project_data.get("top_projects", [])
                logger.info(f"✓ Project relevance: {project_relevance_score}")
            else:
                logger.warning(f"Project relevance API returned {project_response.status_code}")
        except Exception as proj_error:
            logger.warning(f"Failed to fetch project relevance (non-fatal): {proj_error}")
        
        response = AgentRunResponse(
            candidate_id=candidate_id,
            role_key=role_key,
            status="success",
            message=f"Pipeline completed successfully for {candidate_id}",
            normalized_skills_count=normalized_skills_count,
            nodes_created=write_result.nodes_created,
            relationships_created=write_result.relationships_created,
            skill_confidence_top=gap_result.get("skill_confidence_top", []),
            skill_gap_top=gap_result.get("skill_gap_top", []),
            readiness_score=gap_result.get("readiness_score"),
            project_relevance_score=project_relevance_score,
            relevant_projects=relevant_projects,
            xai=xai_result
        )
        
        logger.info(
            f"✓ Pipeline complete: {write_result.nodes_created} nodes, "
            f"{write_result.relationships_created} relationships, "
            f"readiness={response.readiness_score:.2f}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@app.post("/agent/run-from-pdf", response_model=AgentRunResponse, tags=["Agent"])
async def run_agent_from_pdf(
    cv_file: UploadFile = File(..., description="CV/Resume PDF file"),
    role_key: str = Query(..., description="Target role key for gap analysis (e.g., 'ai_ml_engineer')"),
    top_k: int = Query(25, ge=1, le=100, description="Number of top skill deficits to return"),
    include_xai: bool = Query(True, description="Include explainability analysis (skill-level + SHAP)"),
    ranking_method: str = Query(
        None,
        description="Ranking method: 'symbolic' (TF-IDF), 'hybrid' (GNN × importance × gap), or 'additive_gnn'. Default: from config (currently 'hybrid')"
    )
):
    """
    Run complete agentic pipeline from uploaded PDF/DOCX resume.
    
    **NEW: PDF Upload Support with Free LLM Parsing**
    
    **Pipeline:**
    
    1. **CV Parser Service**: Extract text from PDF → Structure with LLM (Open Router/Gemini)
    2. **Extractor Agent**: Validates extracted data
    3. **Normalizer Agent**: Maps skills to canonical names
    4. **KG Writer Tool**: Creates/updates candidate graph in Neo4j
    5. **Gap Analyzer Tool**: Runs skill confidence & gap analysis
    
    **LLM Parsing Strategy:**
    - Primary: Open Router Llama 3.1 70B (free, best quality)
    - Fallback 1: Open Router Llama 3.1 8B (free, faster)
    - Fallback 2: Google Gemini Flash (free, reliable)
    
    **File Support:**
    - PDF (native or scanned)
    - Text extraction: pdfplumber (fast) → OCR fallback (scanned PDFs)
    - Max size: 10MB
    
    Args:
        cv_file: Uploaded CV/Resume file
        role_key: Target role key for gap analysis
        top_k: Number of top deficits to return
        include_xai: Whether to include XAI analysis
        ranking_method: Override default ranking method (optional)
        
    Returns:
        AgentRunResponse with complete pipeline results
    """
    logger.info(f"📤 PDF upload received: {cv_file.filename} ({cv_file.content_type})")
    
    # Validate file type
    content_type = cv_file.content_type or ""
    valid_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if not any(t in content_type for t in valid_types):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Please upload PDF or DOCX."
        )
    
    # Read file bytes
    try:
        pdf_bytes = await cv_file.read()
        file_size_mb = len(pdf_bytes) / (1024 * 1024)
        
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if file_size_mb > 10:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.1f}MB (max 10MB)"
            )
        
        logger.info(f"✓ File validated: {file_size_mb:.2f}MB")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")
    
    # Parse PDF to ExtractedData
    try:
        logger.info("🤖 Parsing CV with LLM...")
        cv_parser = get_cv_parser_service()
        cv_data = await cv_parser.parse_cv_pdf(pdf_bytes, cv_file.filename)
        logger.info(f"✓ CV parsed: {cv_data.candidate_id} ({cv_data.num_skills} skills)")
        
    except Exception as e:
        logger.error(f"❌ CV parsing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse CV: {str(e)}"
        )
    
    # Continue with existing pipeline
    try:
        logger.info(
            f"🤖 Agent pipeline started: candidate={cv_data.candidate_id}, "
            f"role={role_key}, ranking={ranking_method or SKILL_GAP_RANKING_METHOD}"
        )
        
        candidate_id = cv_data.candidate_id
        
        # Step 1: Extractor Agent
        logger.info("Step 1/4: Extractor Agent")
        validated_data = extractor.extract(cv_data)
        
        # Step 2: Normalizer Agent
        logger.info("Step 2/4: Normalizer Agent")
        normalized_data = normalizer.normalize_extracted_data(validated_data)
        normalized_skills_count = len(normalized_data.all_skills) if normalized_data.all_skills else 0
        
        # Step 3: KG Writer Tool
        logger.info("Step 3/4: KG Writer Tool")
        with Neo4jConnection.get_session() as session:
            write_result = KGWriterTool.write_candidate(session, normalized_data)
        
        if not write_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to write to Neo4j: {write_result.message}"
            )
        
        # Step 4: Gap Analyzer Tool
        logger.info("Step 4/4: Gap Analyzer Tool")
        effective_ranking_method = ranking_method or SKILL_GAP_RANKING_METHOD
        request_gap_analyzer = GapAnalyzerTool(ranking_method=effective_ranking_method)
        
        gap_result = request_gap_analyzer.analyze_gap(
            candidate_id=candidate_id,
            role_key=role_key,
            top_k=top_k
        )
        
        logger.info(f"Gap analysis complete using '{effective_ranking_method}' method")
        
        # Step 5: XAI (Optional)
        xai_result = None
        if include_xai:
            logger.info("Step 5/5: Computing XAI")
            try:
                deficits_dict = [
                    {
                        "skill_name": d.skill_name,
                        "deficit": d.deficit,
                        "importance": d.importance,
                        "p_has": d.match_strength
                    }
                    for d in gap_result.get("skill_gap_top", [])
                ]
                
                skill_contributions = xai_service.compute_skill_level_explanation(
                    deficits_dict,
                    top_n=10
                )
                
                total_deficit = sum(d["deficit"] for d in deficits_dict)
                
                skill_level_xai = SkillExplainResponse(
                    candidate_id=candidate_id,
                    role_key=role_key,
                    top_contributors=[
                        SkillContribution(**c) for c in skill_contributions
                    ],
                    total_deficit=round(total_deficit, 4)
                )
                
                with Neo4jConnection.get_session() as session:
                    feature_row = xai_service.build_feature_row(
                        session,
                        candidate_id,
                        role_key
                    )
                
                if feature_row is not None:
                    shap_explanation = xai_service.compute_shap_explanation(
                        feature_row,
                        top_k=5
                    )
                    
                    if shap_explanation.get("enabled"):
                        shap_explanation["candidate_id"] = candidate_id
                        shap_explanation["role_key"] = role_key
                    
                    shap_level_xai = FriendlyPredictExplainResponse(**shap_explanation)
                else:
                    shap_level_xai = FriendlyPredictExplainResponse(
                        enabled=False,
                        reason="Failed to build feature row"
                    )
                
                xai_result = XAIResponse(
                    skill_level=skill_level_xai,
                    shap_level=shap_level_xai
                )
                
                logger.info("✓ XAI computed successfully")
                
            except Exception as xai_error:
                logger.warning(f"XAI computation failed (non-fatal): {xai_error}")
                xai_result = None
        
        # Step 6: Project Relevance
        project_relevance_score = None
        relevant_projects = None
        
        try:
            logger.info("Fetching project relevance...")
            project_url = f"{RECOMMENDATION_API_BASE_URL}/candidates/{candidate_id}/roles/{role_key}/project-relevance"
            project_response = requests.get(project_url, params={"top_n": 5, "top_k": 25}, timeout=5)
            
            if project_response.status_code == 200:
                project_data = project_response.json()
                project_relevance_score = project_data.get("candidate_project_score")
                relevant_projects = project_data.get("top_projects", [])
                logger.info(f"✓ Project relevance: {project_relevance_score}")
            else:
                logger.warning(f"Project relevance API returned {project_response.status_code}")
        except Exception as proj_error:
            logger.warning(f"Failed to fetch project relevance (non-fatal): {proj_error}")
        
        response = AgentRunResponse(
            candidate_id=candidate_id,
            role_key=role_key,
            status="success",
            message=f"Pipeline completed from PDF: {cv_file.filename}",
            normalized_skills_count=normalized_skills_count,
            nodes_created=write_result.nodes_created,
            relationships_created=write_result.relationships_created,
            skill_confidence_top=gap_result.get("skill_confidence_top", []),
            skill_gap_top=gap_result.get("skill_gap_top", []),
            readiness_score=gap_result.get("readiness_score"),
            project_relevance_score=project_relevance_score,
            relevant_projects=relevant_projects,
            xai=xai_result
        )
        
        logger.info(f"🤖 Pipeline complete from PDF: {candidate_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


# ============================================================================
# Utility Endpoints (Optional)
# ============================================================================

@app.get("/aliases", tags=["Utilities"])
def get_skill_aliases():
    """
    Get all configured skill aliases.
    
    Returns dictionary of alias -> canonical name mappings.
    Useful for debugging normalization.
    """
    return {
        "total_aliases": len(normalizer.get_all_aliases()),
        "aliases": normalizer.get_all_aliases()
    }


@app.post("/aliases/add", tags=["Utilities"])
def add_skill_alias(alias: str, canonical: str):
    """
    Add a new skill alias at runtime.
    
    Args:
        alias: Alias name (e.g., "python3")
        canonical: Canonical name (e.g., "Python")
        
    Returns:
        Confirmation message
    """
    normalizer.add_alias(alias, canonical)
    return {
        "status": "success",
        "message": f"Added alias: {alias} -> {canonical}"
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )
