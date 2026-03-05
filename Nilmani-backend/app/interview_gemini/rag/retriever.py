"""
RAG Retriever Module
Retrieves relevant context from FAISS vector store
"""
from langchain_community.vectorstores import FAISS
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def retrieve_context(vector_store: FAISS, query: str, k: int = 4) -> str:
    """
    Retrieve relevant context from vector store based on query.
    
    Args:
        vector_store: FAISS vector store instance
        query: Query string to search for
        k: Number of top documents to retrieve (default: 4)
    
    Returns:
        str: Combined text from retrieved documents
    
    Raises:
        Exception: If retrieval fails
    """
    if not vector_store:
        raise ValueError("Vector store is required for retrieval")
    
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    try:
        logger.debug(f"Retrieving top {k} documents for query: '{query[:50]}...'")
        
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        docs = retriever.invoke(query)
        
        if not docs:
            logger.warning(f"No documents retrieved for query: {query}")
            return ""
        
        # Combine document contents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        logger.info(f"Retrieved {len(docs)} documents, total {len(context)} characters")
        
        return context
        
    except Exception as e:
        logger.error(f"Context retrieval failed: {str(e)}")
        raise Exception(f"Failed to retrieve context: {str(e)}")


def retrieve_with_scores(vector_store: FAISS, query: str, k: int = 4) -> List[Dict]:
    """
    Retrieve documents with similarity scores.
    
    Args:
        vector_store: FAISS vector store instance
        query: Query string to search for
        k: Number of top documents to retrieve
    
    Returns:
        List[Dict]: List of dicts with 'content' and 'score'
    
    Raises:
        Exception: If retrieval fails
    """
    try:
        results = vector_store.similarity_search_with_score(query, k=k)
        
        formatted_results = [
            {
                "content": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata
            }
            for doc, score in results
        ]
        
        logger.info(f"Retrieved {len(formatted_results)} documents with scores")
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Scored retrieval failed: {str(e)}")
        raise Exception(f"Failed to retrieve with scores: {str(e)}")
