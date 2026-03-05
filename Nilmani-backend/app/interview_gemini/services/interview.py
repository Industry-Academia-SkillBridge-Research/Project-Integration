"""
Interview Engine Module
Orchestrates the RAG-based interview process:
1. Retrieves relevant JD context from FAISS (using LOCAL Ollama embeddings)
2. Generates questions using Google Gemini (text generation only)
"""
from app.interview_gemini.llm.gemini import get_llm, generate_text
from app.interview_gemini.llm.prompt import INTERVIEW_PROMPT
from app.interview_gemini.rag.retriever import retrieve_context
from app.core.config import MAX_QUESTIONS
import logging

logger = logging.getLogger(__name__)

# Initialize Gemini LLM (for text generation only)
llm = get_llm()


def generate_next_turn(session: dict, user_answer: str = None) -> tuple:
    """
    Generate next interview turn using RAG approach.
    
    Process:
    1. Retrieve relevant JD chunks from FAISS (using LOCAL Ollama embeddings)
    2. Send context + history to Gemini for question generation
    3. Update session state
    
    Args:
        session: Interview session dict containing vector_store, history, etc.
        user_answer: Optional user's answer to previous question
    
    Returns:
        tuple: (question, feedback, ended)
            - question: Next question or None if ended
            - feedback: Feedback on previous answer or None
            - ended: Boolean indicating if interview has ended
    
    Raises:
        Exception: If generation fails
    """
    try:
        # Check if interview already ended
        if session.get("ended", False):
            logger.info("Interview already ended")
            return None, None, True
        
        # Add user answer to history
        if user_answer:
            session["history"].append(f"Candidate: {user_answer}")
            logger.debug(f"Added user answer to history: {user_answer[:50]}...")
        
        # Check if max questions reached
        questions_asked = session.get("questions_asked", 0)
        if questions_asked >= MAX_QUESTIONS:
            logger.info(f"Max questions ({MAX_QUESTIONS}) reached. Ending interview.")
            session["ended"] = True
            return None, "Thank you for participating in this interview!", True
        
        # Retrieve relevant context from JD using RAG
        # This uses LOCAL Ollama embeddings, NOT cloud API
        vector_store = session.get("vector_store")
        if not vector_store:
            raise ValueError("Vector store not found in session")
        
        context = retrieve_context(
            vector_store,
            query="job responsibilities, required skills, qualifications, and experience",
            k=4
        )
        
        if not context:
            logger.warning("No context retrieved from vector store, using empty context")
            context = "No specific job description context available."
        
        # Build prompt for Gemini
        history_text = "\n".join(session.get("history", []))
        prompt = INTERVIEW_PROMPT.format(
            context=context,
            history=history_text if history_text else "No conversation yet."
        )
        
        logger.debug("Sending prompt to Gemini for question generation")
        
        # Generate response using Gemini (text generation only)
        response = generate_text(llm, prompt)
        
        # Update session state
        session["questions_asked"] = questions_asked + 1
        session["history"].append(f"Interviewer: {response}")
        session["question_count"] = session["questions_asked"]  # For API compatibility
        
        logger.info(
            f"Generated question {session['questions_asked']}/{MAX_QUESTIONS}"
        )
        
        # Parse response (simple version - can be enhanced)
        feedback = None
        question = response
        
        return question, feedback, False
        
    except Exception as e:
        logger.error(f"Failed to generate next turn: {str(e)}")
        raise Exception(f"Interview generation failed: {str(e)}")


def end_interview(session: dict) -> str:
    """
    End interview session and provide summary.
    
    Args:
        session: Interview session dict
    
    Returns:
        str: Interview summary message
    """
    session["ended"] = True
    questions_asked = session.get("questions_asked", 0)
    
    summary = (
        f"Interview completed. "
        f"You answered {questions_asked} question(s). "
        f"Thank you for your time!"
    )
    
    logger.info(f"Interview ended: {questions_asked} questions asked")
    
    return summary
