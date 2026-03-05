"""
Text Chunking Module
Splits text into chunks for embedding and retrieval
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
import logging

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Chunk text using RecursiveCharacterTextSplitter.
    Optimized chunk size to balance context quality and embedding efficiency.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum size of each chunk (default: 1000 for better context)
        chunk_overlap: Overlap between chunks to maintain context continuity
    
    Returns:
        List[str]: List of text chunks
    
    Raises:
        ValueError: If text is empty
    """
    if not text or not text.strip():
        raise ValueError("Cannot chunk empty text")
    
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        
        logger.info(
            f"Text chunked into {len(chunks)} chunks "
            f"(size={chunk_size}, overlap={chunk_overlap})"
        )
        
        # Log chunk statistics
        if chunks:
            avg_size = sum(len(c) for c in chunks) / len(chunks)
            logger.debug(f"Average chunk size: {avg_size:.0f} characters")
        
        return chunks
        
    except Exception as e:
        logger.error(f"Text chunking failed: {str(e)}")
        raise Exception(f"Failed to chunk text: {str(e)}")
