"""
Advanced Skill Gap & Course Recommendation API
==============================================

Main application entry point with FastAPI.

Architecture:
- config/: Configuration and constants
- models/: Pydantic schemas for validation
- database/: Neo4j connection management
- services/: Business logic (confidence, importance, deficit, recommendation, GNN)
- routes/: FastAPI route handlers
- utils/: Cache and helper utilities
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import API_TITLE, API_VERSION, API_DESCRIPTION, LOG_LEVEL, LOG_FORMAT
from database import Neo4jConnection
from routes import router
from services.gnn_inference_service import gnn_service
from xai.api import router as xai_router, initialize_xai_service

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
    
    Startup:
        - Initialize Neo4j connection
        - Load GNN model and graph data
    
    Shutdown:
        - Close Neo4j connection
    """
    # Startup
    logger.info("Starting Advanced Recommendation API with GNN support...")
    try:
        # Initialize Neo4j connection
        Neo4jConnection.get_driver()
        logger.info("[OK] Neo4j connection initialized")
        
        # Initialize XAI service
        logger.info("Initializing XAI service...")
        initialize_xai_service()
        
        # Load GNN model
        logger.info("Loading GNN model for link prediction...")
        try:
            # GNN-Link-Prediction is in the Advanced-Recommendation-System folder
            base_path = Path(__file__).parent / "GNN-Link-Prediction"
            model_path = str(base_path / "models" / "best_gnn_linkpred.pt")
            data_path = str(base_path / "output" / "heterodata_lp.pt")
            id_maps_path = str(base_path / "output" / "id_maps.json")
            
            gnn_service.load_model(model_path, data_path, id_maps_path)
            logger.info("[OK] GNN model loaded successfully")
            logger.info(f"  - Stats: {gnn_service.get_stats()}")
        except Exception as e:
            logger.warning(f"[SKIP] GNN model loading failed (non-critical): {e}")
            logger.warning("  - GNN-powered features will not be available")
            logger.warning("  - Basic recommendations will still work")
        
        logger.info("[OK] Application startup complete")
    except Exception as e:
        logger.error(f"[FAIL] Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    Neo4jConnection.close()
    logger.info("[OK] Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

# Configure CORS - Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)
app.include_router(xai_router, prefix="/xai", tags=["Explainability"])


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Recommendation Engine"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
