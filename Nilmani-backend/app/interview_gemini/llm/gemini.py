"""
Google Gemini LLM Client Module
Uses Gemini ONLY for text generation (questions, feedback)
NOT for embeddings - embeddings handled by Ollama
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from typing import Any
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = settings.GEMINI_API_KEY
CHAT_MODEL = settings.CHAT_MODEL


def extract_text_from_gemini(response: Any) -> str:
    """
    Safely extract plain text string from Gemini response object.
    
    Handles multiple response formats:
    - response.text (simple string attribute)
    - response.candidates[0].content.parts (list of content parts)
    - response.content (string or list)
    - Direct string responses
    
    Args:
        response: Gemini response object (various formats)
    
    Returns:
        str: Extracted text as a single plain string
    
    Raises:
        ValueError: If no valid text can be extracted from response
    """
    try:
        # Method 1: Try response.text (most common)
        if hasattr(response, 'text') and response.text:
            text = str(response.text).strip()
            logger.debug(f"Extracted from response.text: {text[:100]}...")
            return text
        
        # Method 2: Try response.content (LangChain format)
        if hasattr(response, 'content'):
            content = response.content
            
            # Handle content as list of parts
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    # Handle dict with 'text' key
                    if isinstance(item, dict):
                        if item.get('type') == 'text' and 'text' in item:
                            text_parts.append(str(item['text']))
                        elif 'text' in item:
                            text_parts.append(str(item['text']))
                    # Handle object with text attribute
                    elif hasattr(item, 'text'):
                        text_parts.append(str(item.text))
                    # Handle plain string in list
                    elif isinstance(item, str):
                        text_parts.append(item)
                
                if text_parts:
                    text = ' '.join(text_parts).strip()
                    logger.debug(f"Extracted from content list: {text[:100]}...")
                    return text
            
            # Handle content as string
            elif isinstance(content, str) and content.strip():
                text = content.strip()
                logger.debug(f"Extracted from content string: {text[:100]}...")
                return text
        
        # Method 3: Try response.candidates[0].content.parts (native Gemini format)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                text_parts = []
                for part in parts:
                    if hasattr(part, 'text'):
                        text_parts.append(str(part.text))
                
                if text_parts:
                    text = ' '.join(text_parts).strip()
                    logger.debug(f"Extracted from candidates.parts: {text[:100]}...")
                    return text
        
        # Method 4: Try converting entire response to string as last resort
        if response is not None:
            text = str(response).strip()
            if text and len(text) > 0:
                logger.warning(f"Used fallback str() conversion: {text[:100]}...")
                return text
        
        # If all methods fail, raise error
        logger.error(f"Failed to extract text from response type: {type(response)}")
        logger.error(f"Response attributes: {dir(response)}")
        raise ValueError(
            f"Unable to extract text from Gemini response. "
            f"Response type: {type(response)}. "
            f"This may indicate an API format change or error."
        )
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in extract_text_from_gemini: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to parse Gemini response: {str(e)}")


def get_llm():
    """
    Initialize Google Gemini LLM for text generation only.
    
    Returns:
        ChatGoogleGenerativeAI: Configured Gemini chat model
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required but not set in environment variables")
    
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0.7,
        google_api_key=GEMINI_API_KEY,
        max_output_tokens=512,
        timeout=30
    )


def generate_text(llm, prompt: str) -> str:
    """
    Generate text using Gemini LLM with robust response handling.
    
    Args:
        llm: Initialized Gemini LLM instance
        prompt: The prompt to send to the model
    
    Returns:
        str: Generated text response as a plain string
    
    Raises:
        ValueError: If text extraction fails
        Exception: If API call fails
    """
    try:
        logger.debug("Invoking Gemini LLM...")
        response = llm.invoke(prompt)
        logger.debug(f"Gemini response type: {type(response)}")
        
        # Use the robust extractor to get plain text
        text = extract_text_from_gemini(response)
        
        if not text or not text.strip():
            raise ValueError("Gemini returned empty response")
        
        logger.info(f"Successfully generated text ({len(text)} chars)")
        return text.strip()
        
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error in generate_text: {str(e)}", exc_info=True)
        raise Exception(f"Gemini API error during text generation: {str(e)}")
