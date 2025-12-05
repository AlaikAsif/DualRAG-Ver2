"""Static RAG endpoints for document retrieval and search."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from src.chains.static_rag_chain import StaticRAGChain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/static-rag", tags=["Static RAG"])

# Global instance
_static_rag_chain: Optional[StaticRAGChain] = None


def set_static_rag_chain(chain: StaticRAGChain):
    """Set the global StaticRAGChain instance."""
    global _static_rag_chain
    _static_rag_chain = chain


def get_static_rag_chain() -> StaticRAGChain:
    """Dependency to get StaticRAGChain instance."""
    if _static_rag_chain is None:
        raise HTTPException(
            status_code=503,
            detail="Static RAG service not available. Vector store not initialized."
        )
    return _static_rag_chain


# Request/Response Models
class StaticRAGRequest(BaseModel):
    """Request model for static RAG queries."""
    query: str
    top_k: Optional[int] = 5
    threshold: Optional[float] = None


class RetrievedDocument(BaseModel):
    """Retrieved document with relevance score."""
    content: str
    score: float
    metadata: Optional[dict] = None


class StaticRAGResponse(BaseModel):
    """Response model for static RAG queries."""
    query: str
    documents: List[RetrievedDocument]
    total_retrieved: int


class IndexStatusResponse(BaseModel):
    """Response for vector store status."""
    indexed: bool
    document_count: Optional[int] = None
    last_updated: Optional[str] = None


# Endpoints
@router.post(
    "/retrieve",
    response_model=StaticRAGResponse,
    summary="Retrieve documents from static RAG",
    description="Query the vector store to retrieve relevant documents"
)
async def retrieve_documents(
    request: StaticRAGRequest,
    chain: StaticRAGChain = Depends(get_static_rag_chain)
) -> StaticRAGResponse:
    """
    Retrieve documents from the vector store based on query.
    
    Args:
        request: Query request with search parameters
        chain: StaticRAGChain instance (injected)
        
    Returns:
        StaticRAGResponse with retrieved documents and scores
    """
    try:
        logger.info(f"Retrieving documents for query: {request.query}")
        
        # Retrieve documents from the chain
        results = chain.retrieve(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        # Convert results to response model
        documents = [
            RetrievedDocument(
                content=doc.get("content", ""),
                score=doc.get("score", 0.0),
                metadata=doc.get("metadata")
            )
            for doc in results
        ]
        
        logger.info(f"Retrieved {len(documents)} documents")
        return StaticRAGResponse(
            query=request.query,
            documents=documents,
            total_retrieved=len(documents)
        )
    
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search",
    response_model=StaticRAGResponse,
    summary="Search documents",
    description="Search the vector store for documents matching query"
)
async def search_documents(
    query: str,
    top_k: int = 5,
    chain: StaticRAGChain = Depends(get_static_rag_chain)
) -> StaticRAGResponse:
    """
    Search documents in the vector store.
    
    Args:
        query: Search query string
        top_k: Number of top results to return
        chain: StaticRAGChain instance (injected)
        
    Returns:
        StaticRAGResponse with matching documents
    """
    try:
        logger.info(f"Searching for: {query}")
        
        results = chain.retrieve(query=query, top_k=top_k)
        
        documents = [
            RetrievedDocument(
                content=doc.get("content", ""),
                score=doc.get("score", 0.0),
                metadata=doc.get("metadata")
            )
            for doc in results
        ]
        
        return StaticRAGResponse(
            query=query,
            documents=documents,
            total_retrieved=len(documents)
        )
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/index",
    response_model=dict,
    summary="Index documents",
    description="Add or update documents in the vector store"
)
async def index_documents(
    documents: List[dict],
    chain: StaticRAGChain = Depends(get_static_rag_chain)
) -> dict:
    """
    Index documents in the vector store.
    
    Args:
        documents: List of documents to index
        chain: StaticRAGChain instance (injected)
        
    Returns:
        Status message with number of indexed documents
    """
    try:
        logger.info(f"Indexing {len(documents)} documents")
        
        result = chain.index(documents)
        
        logger.info(f"Successfully indexed {len(documents)} documents")
        return {
            "status": "success",
            "message": f"Indexed {len(documents)} documents",
            "count": len(documents)
        }
    
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=IndexStatusResponse,
    summary="Get vector store status",
    description="Check the status of the vector store and index"
)
async def get_index_status(
    chain: StaticRAGChain = Depends(get_static_rag_chain)
) -> IndexStatusResponse:
    """
    Get the current status of the vector store.
    
    Returns:
        IndexStatusResponse with vector store metadata
    """
    try:
        logger.info("Fetching vector store status")
        
        status = chain.get_status()
        
        return IndexStatusResponse(
            indexed=status.get("indexed", False),
            document_count=status.get("document_count"),
            last_updated=status.get("last_updated")
        )
    
    except Exception as e:
        logger.error(f"Error getting index status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/clear",
    response_model=dict,
    summary="Clear vector store",
    description="Clear all documents from the vector store"
)
async def clear_index(
    chain: StaticRAGChain = Depends(get_static_rag_chain)
) -> dict:
    """
    Clear all documents from the vector store.
    
    Returns:
        Status message confirming clear operation
    """
    try:
        logger.info("Clearing vector store")
        
        chain.clear()
        
        logger.info("Vector store cleared successfully")
        return {
            "status": "success",
            "message": "Vector store cleared successfully"
        }
    
    except Exception as e:
        logger.error(f"Error clearing vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
