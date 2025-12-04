"""
RAG Query and Response Schemas.

Defines Pydantic models for RAG (Retrieval-Augmented Generation) inputs and outputs.
These schemas enforce type safety and validation across RAG chain components.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SourceDocument(BaseModel):
    """Retrieved document with content and metadata."""
    
    content: str = Field(..., description="Document text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata (source, page, etc.)")
    score: float = Field(default=0.0, description="Retrieval similarity score (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a sample document chunk.",
                "metadata": {"source": "document.pdf", "page": 1},
                "score": 0.87
            }
        }


class RAGRequest(BaseModel):
    """RAG query request."""
    
    query: str = Field(..., description="User query string")
    retrieval_k: int = Field(default=3, ge=1, le=20, description="Number of documents to retrieve")
    use_mmr: bool = Field(default=True, description="Enable MMR reranking for diversity")
    include_sources: bool = Field(default=True, description="Include source documents in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the main purpose of this document?",
                "retrieval_k": 3,
                "use_mmr": True,
                "include_sources": True
            }
        }


class RAGResponse(BaseModel):
    """RAG response with generated text and source documents."""
    
    response: str = Field(..., description="Generated response text")
    source_documents: List[SourceDocument] = Field(default_factory=list, description="Retrieved source documents")
    retrieval_count: int = Field(default=0, ge=0, description="Number of documents retrieved")
    chain_name: str = Field(default="static_rag", description="Name of the chain that generated this response")
    model_name: Optional[str] = Field(default=None, description="Name of the model used for generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on the provided documents, the main purpose is...",
                "source_documents": [
                    {
                        "content": "Document content...",
                        "metadata": {"source": "doc.pdf", "page": 1},
                        "score": 0.85
                    }
                ],
                "retrieval_count": 1,
                "chain_name": "static_rag",
                "model_name": "granite3-dense:8b"
            }
        }


class RetrievalResult(BaseModel):
    """Intermediate retrieval result (before LLM generation)."""
    
    documents: List[SourceDocument] = Field(..., description="Retrieved documents")
    query: str = Field(..., description="Original query")
    retrieval_method: str = Field(default="mmr", description="Method used (mmr or similarity)")
    retrieval_time_ms: float = Field(default=0.0, description="Time to retrieve documents in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {"content": "...", "metadata": {}, "score": 0.8}
                ],
                "query": "test query",
                "retrieval_method": "mmr",
                "retrieval_time_ms": 125.5
            }
        }


class RAGPipeline(BaseModel):
    """Full RAG pipeline configuration."""
    
    index_path: str = Field(default="data/vectors/static/index", description="Path to FAISS index")
    retrieval_k: int = Field(default=3, ge=1, le=20, description="Documents to retrieve")
    initial_k: int = Field(default=10, ge=1, description="Candidates before MMR reranking")
    use_mmr: bool = Field(default=True, description="Enable MMR reranking")
    llm_model: str = Field(default="granite3-dense:8b", description="LLM model name")
    llm_url: str = Field(default="http://localhost:11434", description="LLM server URL")
    chunk_size: int = Field(default=400, ge=100, description="Document chunk size")
    chunk_overlap: int = Field(default=100, ge=0, description="Chunk overlap")
    
    class Config:
        json_schema_extra = {
            "example": {
                "index_path": "data/vectors/static/index",
                "retrieval_k": 3,
                "initial_k": 10,
                "use_mmr": True,
                "llm_model": "granite3-dense:8b",
                "llm_url": "http://localhost:11434",
                "chunk_size": 400,
                "chunk_overlap": 100
            }
        }
