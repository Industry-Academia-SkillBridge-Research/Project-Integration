"""
FAISS Vector Store Module
Handles vector store creation, saving, and loading using LOCAL Ollama embeddings
"""
from langchain_community.vectorstores import FAISS
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def create_vector_store(chunks: List[str], embeddings, save_path: Optional[Path] = None):
    """
    Create FAISS vector store from text chunks using LOCAL Ollama embeddings.
    No cloud API calls - all embeddings generated locally.
    
    Args:
        chunks: List of text chunks to embed
        embeddings: Ollama embeddings instance (OllamaEmbeddings)
        save_path: Optional path to save the vector store
    
    Returns:
        FAISS: Created vector store
    
    Raises:
        ValueError: If chunks are empty
        Exception: If embedding or vector store creation fails
    """
    if not chunks:
        raise ValueError("Cannot create vector store from empty chunks")
    
    try:
        logger.info(f"Creating FAISS vector store from {len(chunks)} chunks using LOCAL Ollama embeddings...")
        
        # Create vector store - all embeddings done locally via Ollama
        vector_store = FAISS.from_texts(chunks, embeddings)
        
        logger.info("Vector store created successfully using LOCAL embeddings")
        
        # Save if path provided
        if save_path:
            save_vector_store(vector_store, save_path)
        
        return vector_store
        
    except Exception as e:
        error_msg = (
            f"Failed to create vector store. "
            f"Ensure Ollama is running and embeddings are available. "
            f"Error: {str(e)}"
        )
        logger.error(error_msg)
        raise Exception(error_msg)


def save_vector_store(vector_store: FAISS, save_path: Path) -> None:
    """
    Save FAISS vector store to disk.
    
    Args:
        vector_store: The FAISS vector store to save
        save_path: Directory path to save the vector store
    
    Raises:
        Exception: If saving fails
    """
    try:
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        vector_store.save_local(str(save_path))
        logger.info(f"Vector store saved to {save_path}")
        
    except Exception as e:
        logger.error(f"Failed to save vector store: {str(e)}")
        raise Exception(f"Failed to save vector store: {str(e)}")


def load_vector_store(load_path: Path, embeddings) -> FAISS:
    """
    Load FAISS vector store from disk.
    
    Args:
        load_path: Directory path where vector store is saved
        embeddings: Ollama embeddings instance for loading
    
    Returns:
        FAISS: Loaded vector store
    
    Raises:
        FileNotFoundError: If vector store doesn't exist
        Exception: If loading fails
    """
    try:
        load_path = Path(load_path)
        
        if not load_path.exists():
            raise FileNotFoundError(f"Vector store not found at {load_path}")
        
        vector_store = FAISS.load_local(
            str(load_path),
            embeddings,
            allow_dangerous_deserialization=True  # Required for FAISS
        )
        
        logger.info(f"Vector store loaded from {load_path}")
        return vector_store
        
    except Exception as e:
        logger.error(f"Failed to load vector store: {str(e)}")
        raise Exception(f"Failed to load vector store: {str(e)}")
