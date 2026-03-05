"""
Local Embeddings Module using Ollama
Uses Ollama's nomic-embed-text model for LOCAL embeddings
NO cloud API calls for embeddings
"""
from langchain_ollama import OllamaEmbeddings
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def get_local_embeddings():
    """
    Initialize Ollama embeddings for LOCAL embedding generation.
    Uses nomic-embed-text model running on local Ollama instance.
    
    Returns:
        OllamaEmbeddings: Configured Ollama embeddings instance
    
    Raises:
        Exception: If Ollama is not running or model is not available
    """
    try:
        embeddings = OllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_EMBEDDING_MODEL
        )
        
        logger.info(f"Initialized Ollama embeddings: {settings.OLLAMA_EMBEDDING_MODEL}")
        logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
        
        return embeddings
        
    except Exception as e:
        error_msg = (
            f"Failed to initialize Ollama embeddings. "
            f"Ensure Ollama is running at {settings.OLLAMA_BASE_URL} "
            f"and model '{settings.OLLAMA_EMBEDDING_MODEL}' is installed. "
            f"Error: {str(e)}"
        )
        logger.error(error_msg)
        raise Exception(error_msg)


def test_embeddings_connection():
    """
    Test if Ollama embeddings are working properly.
    
    Returns:
        bool: True if embeddings work, False otherwise
    """
    try:
        embeddings = get_local_embeddings()
        # Test with a simple embedding
        test_text = "Test embedding connection"
        _ = embeddings.embed_query(test_text)
        logger.info("Ollama embeddings test successful")
        return True
    except Exception as e:
        logger.error(f"Ollama embeddings test failed: {str(e)}")
        return False
