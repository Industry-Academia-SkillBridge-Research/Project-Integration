"""
FastAPI server for AI-Powered Interview Training System
Provides REST API endpoints for frontend integration
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
import tempfile
import os
import uvicorn

from app.interview_gemini.rag.embeddings import get_local_embeddings
from app.interview_gemini.rag.loader import chunk_text
from app.interview_gemini.rag.vector_store import create_vector_store
from app.interview_gemini.utils.session import create_session, get_session
from app.interview_gemini.services.interview import generate_next_turn
from app.core.config import settings


# Initialize FastAPI app
app = FastAPI(
    title="AI Interview Training API",
    description="RAG-based interview training system with Gemini",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # NewFrontend
        "http://localhost:4173",  # Vite preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embeddings
embeddings = get_local_embeddings()

# Global state (in production, use session management or Redis)
sessions = {}


# Pydantic models
class JDUploadResponse(BaseModel):
    session_id: str
    text: str
    chunks_count: int
    message: str


class QuestionRequest(BaseModel):
    session_id: str
    user_answer: Optional[str] = None


class QuestionResponse(BaseModel):
    question: str
    question_number: int
    total_questions: int
    is_complete: bool


class SessionStatus(BaseModel):
    session_id: str
    is_active: bool
    question_count: int
    max_questions: int


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Interview Training API",
        "chat_model": settings.CHAT_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Gemini API
        return {
            "status": "healthy",
            "gemini": "connected",
            "chat_model": settings.CHAT_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/api/upload-jd", response_model=JDUploadResponse)
async def upload_jd(file: UploadFile = File(...)):
    """
    Upload job description PDF and initialize RAG vector store
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Extract text from PDF (using fitz/PyMuPDF)
        doc = fitz.open(tmp_path)
        jd_text = ""
        for page in doc:
            jd_text += page.get_text()
        doc.close()
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if not jd_text or len(jd_text) < 50:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from PDF")
        
        # Chunk text and create vector store
        chunks = chunk_text(jd_text)
        vector_store = create_vector_store(chunks, embeddings)
        
        # Create session
        session_id = create_session(vector_store)
        
        # Store additional session info
        sessions[session_id] = {
            "jd_text": jd_text,
            "filename": file.filename,
            "chunks_count": len(chunks)
        }
        
        return JDUploadResponse(
            session_id=session_id,
            text=jd_text[:500] + "..." if len(jd_text) > 500 else jd_text,
            chunks_count=len(chunks),
            message="Job description processed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/api/start-interview", response_model=QuestionResponse)
async def start_interview(request: QuestionRequest):
    """
    Start interview and get first question
    """
    try:
        session = get_session(request.session_id)
        
        # Get first question
        question, _, _ = generate_next_turn(session)
        
        return QuestionResponse(
            question=question,
            question_number=session["question_count"],
            total_questions=settings.MAX_INTERVIEW_QUESTIONS,
            is_complete=False
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")


@app.post("/api/next-question", response_model=QuestionResponse)
async def next_question(request: QuestionRequest):
    """
    Submit answer and get next question
    """
    if not request.user_answer:
        raise HTTPException(status_code=400, detail="Answer is required")
    
    try:
        session = get_session(request.session_id)
        
        # Get next question based on answer
        question, feedback, ended = generate_next_turn(
            session,
            user_answer=request.user_answer
        )
        
        return QuestionResponse(
            question=question if not ended else "",
            question_number=session["question_count"],
            total_questions=settings.MAX_INTERVIEW_QUESTIONS,
            is_complete=ended
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")


@app.get("/api/session/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """
    Get session status
    """
    try:
        session = get_session(session_id)
        
        return SessionStatus(
            session_id=session_id,
            is_active=session["question_count"] < settings.MAX_INTERVIEW_QUESTIONS,
            question_count=session["question_count"],
            max_questions=settings.MAX_INTERVIEW_QUESTIONS
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    """
    End and cleanup session
    """
    try:
        if session_id in sessions:
            del sessions[session_id]
        return {"message": "Session ended successfully", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")


@app.get("/api/sessions")
async def list_sessions():
    """
    List all active sessions (for debugging)
    """
    return {
        "count": len(sessions),
        "sessions": [
            {
                "session_id": sid,
                "filename": data.get("filename", "unknown"),
                "chunks_count": data.get("chunks_count", 0)
            }
            for sid, data in sessions.items()
        ]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Starting AI Interview Training API Server")
    print("=" * 60)
    print(f"\nAPI URL: http://localhost:8005")
    print(f"Docs: http://localhost:8005/docs")
    print(f"Chat Model: {settings.CHAT_MODEL}")
    print(f"Embeddings: {settings.EMBEDDING_MODEL}\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")