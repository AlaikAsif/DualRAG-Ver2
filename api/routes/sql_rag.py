"""SQL RAG chain API routes."""

from fastapi import APIRouter, HTTPException, Depends
import logging

from src.schemas.sql import SQLRagRequest, SQLRagResponse
from src.chains.sql_rag_chain import SQLRAGChain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["sql-rag"])

_chain_instance = None


def get_sql_rag_chain() -> SQLRAGChain:
    """Dependency to get SQL RAG chain instance."""
    if _chain_instance is None:
        raise HTTPException(
            status_code=503,
            detail="SQL RAG Chain not initialized"
        )
    return _chain_instance


def set_sql_rag_chain(chain: SQLRAGChain):
    """Set the SQL RAG chain instance."""
    global _chain_instance
    _chain_instance = chain


@router.post("/sql-rag", response_model=SQLRagResponse)
async def query_sql_rag(
    request: SQLRagRequest,
    chain: SQLRAGChain = Depends(get_sql_rag_chain)
) -> SQLRagResponse:
    """
    Process natural language query to SQL.

    Args:
        request: SQLRagRequest with natural language query
        chain: SQLRAGChain instance

    Returns:
        SQLRagResponse with generated SQL, explanation, and results
    """
    try:
        response = chain.process(request)
        logger.info(f"Query processed: {request.query[:100]}...")
        return response
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid query: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing SQL RAG request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/schema-summary")
async def schema_summary(chain: SQLRAGChain = Depends(get_sql_rag_chain)):
    """Get database schema summary."""
    try:
        summary = chain.get_schema_summary()
        return {"schema_summary": summary}
    except Exception as e:
        logger.error(f"Error getting schema summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schema: {str(e)}"
        )


@router.post("/schema-refresh")
async def schema_refresh(chain: SQLRAGChain = Depends(get_sql_rag_chain)):
    """Refresh cached database schema."""
    try:
        chain.refresh_schema()
        logger.info("Schema refreshed")
        return {"status": "success", "message": "Schema refreshed"}
    except Exception as e:
        logger.error(f"Error refreshing schema: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh schema: {str(e)}"
        )


@router.get("/execution-history")
async def execution_history(
    limit: int = 10,
    chain: SQLRAGChain = Depends(get_sql_rag_chain)
):
    """Get recent query execution history."""
    try:
        history = chain.get_execution_history()
        return {"history": history[-limit:] if history else []}
    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )

        history = chain.get_execution_history()
        return {
            "execution_history": history[-limit:],
            "total_count": len(history),
            "returned_count": min(limit, len(history))
        }
    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )
