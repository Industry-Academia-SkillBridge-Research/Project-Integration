from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
from . import models
from .routes import (
    admin_router, 
    transcript_router, 
    skills_router, 
    quiz_router,
    admin_question_bank_router,
    admin_question_persistence_router,
    xai_router,
    jobs_router,
    job_router,
    profile_router
)
from ..routes.readiness import router as readiness_router

app = FastAPI(title="Transcript Skill Validation API")

# Create database tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(admin_router)
app.include_router(transcript_router)
app.include_router(skills_router)
app.include_router(quiz_router)
app.include_router(admin_question_bank_router)
app.include_router(admin_question_persistence_router)
app.include_router(xai_router)
app.include_router(jobs_router)
app.include_router(job_router)
app.include_router(profile_router)
app.include_router(readiness_router)

@app.get("/health")
def health():
    return {"status": "ok"}

