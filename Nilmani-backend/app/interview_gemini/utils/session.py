"""
Session Management Module
Handles interview session lifecycle
"""
import uuid
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory session storage
# In production, use Redis or database
sessions: Dict[str, dict] = {}


def create_session(vector_store) -> str:
    """
    Create a new interview session.
    
    Args:
        vector_store: FAISS vector store instance for this session
    
    Returns:
        str: Unique session ID
    """
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "vector_store": vector_store,
        "history": [],
        "questions_asked": 0,
        "question_count": 0,  # For API compatibility
        "ended": False,
        "created_at": None  # Can add timestamp if needed
    }
    
    logger.info(f"Created session: {session_id}")
    
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """
    Retrieve session by ID.
    
    Args:
        session_id: The session ID to retrieve
    
    Returns:
        dict: Session data or None if not found
    
    Raises:
        ValueError: If session not found
    """
    session = sessions.get(session_id)
    
    if not session:
        logger.warning(f"Session not found: {session_id}")
        raise ValueError(f"Session {session_id} not found")
    
    return session


def delete_session(session_id: str) -> bool:
    """
    Delete a session.
    
    Args:
        session_id: The session ID to delete
    
    Returns:
        bool: True if deleted, False if not found
    """
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"Deleted session: {session_id}")
        return True
    
    logger.warning(f"Cannot delete - session not found: {session_id}")
    return False


def get_all_sessions() -> Dict[str, dict]:
    """
    Get all active sessions (for debugging/admin).
    
    Returns:
        Dict: All sessions
    """
    return sessions


def session_exists(session_id: str) -> bool:
    """
    Check if session exists.
    
    Args:
        session_id: The session ID to check
    
    Returns:
        bool: True if exists, False otherwise
    """
    return session_id in sessions
