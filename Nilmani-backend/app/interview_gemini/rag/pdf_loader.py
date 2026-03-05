"""
PDF Loader Module
Handles PDF text extraction and chunking
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Union
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Union[str, Path, bytes]) -> str:
    """
    Extract text from a PDF file or bytes.
    
    Args:
        pdf_path: Path to PDF file, Path object, or PDF bytes
    
    Returns:
        str: Extracted text from all pages
    
    Raises:
        ValueError: If PDF is empty or cannot be read
        Exception: If PDF extraction fails
    """
    try:
        # Handle different input types
        if isinstance(pdf_path, bytes):
            doc = fitz.open(stream=pdf_path, filetype="pdf")
        else:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            doc = fitz.open(pdf_path)
        
        # Extract text from all pages
        text = ""
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            text += page_text
            logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
        
        doc.close()
        
        # Validate extracted text
        if not text or len(text.strip()) < 50:
            raise ValueError(
                f"Insufficient text extracted from PDF. "
                f"Got {len(text)} characters. PDF might be image-based or empty."
            )
        
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text.strip()
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def validate_pdf_content(text: str, min_length: int = 100) -> bool:
    """
    Validate that extracted PDF content is sufficient.
    
    Args:
        text: Extracted text
        min_length: Minimum required text length
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not text:
        logger.warning("PDF content is empty")
        return False
    
    if len(text.strip()) < min_length:
        logger.warning(f"PDF content too short: {len(text)} chars (min: {min_length})")
        return False
    
    return True
