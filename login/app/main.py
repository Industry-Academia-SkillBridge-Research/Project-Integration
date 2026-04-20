"""
FastAPI OAuth 2.0 Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from app.config import settings
from app.database import init_db
from app.routes import auth
from app.routes import candidate
from app.routes import admin

# Create FastAPI application instance
app = FastAPI(
    title="OAuth 2.0 Authentication API with Candidate Data Collection",
    description="Secure OAuth 2.0 login system with Google authentication, JWT tokens, MySQL storage, and AI-driven candidate data collection for skill-gap analysis",
    version="2.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
)

# Add session middleware (required by Authlib for OAuth flow)
# IMPORTANT: Change secret_key in production to a secure random string
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Frontend URLs
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include authentication routes
app.include_router(auth.router)

# Include candidate routes
app.include_router(candidate.router)

# Include admin routes
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    """
    Run on application startup.
    Initialize database tables and storage directories.
    """
    print("[START] Starting OAuth 2.0 Authentication API with Candidate Data Collection...")
    print(f"[DB] Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    print(f"[AUTH] Google OAuth: {'Configured' if settings.GOOGLE_CLIENT_ID else 'Not configured'}")
    print(f"[WEB] Frontend URL: {settings.FRONTEND_URL}")
    print(f"[ENV] Environment: {settings.ENVIRONMENT}")
    print(f"[STORAGE] CV Storage: {settings.CV_STORAGE_PATH}")

    # Initialize database (create tables)
    init_db()
    print("[OK] Database initialized successfully")
    
    # Create storage directories
    from app.services.candidate_service import CandidateService
    CandidateService.create_storage_directories()
    print("[OK] Storage directories created successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown.
    """
    print("[STOP] Shutting down OAuth 2.0 Authentication API...")


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "OAuth 2.0 Authentication API with Candidate Data Collection",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": {
                "login": "/auth/login/google",
                "callback": "/auth/google/callback",
                "current_user": "/auth/me",
                "logout": "/auth/logout",
                "health": "/auth/health",
            },
            "candidate": {
                "init": "POST /candidate/init",
                "status": "GET /candidate/{candidate_id}/status",
                "my_profile": "GET /candidate/me",
                "delete": "DELETE /candidate/me",
                "health": "GET /candidate/health",
            }
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": "oauth-authentication-api",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    # Run the application with Uvicorn
    # In production, use a process manager like systemd or supervisord
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )
