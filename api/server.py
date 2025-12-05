"""FastAPI server for DualRAG chatbot."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.chains.sql_rag_chain import SQLRAGChain
from src.chains.static_rag_chain import StaticRAGChain
from src.utils.config import Config
from api.middleware.error_handling import error_handler_middleware
from api.middleware.logging import logging_middleware
from api.routes import health, sql_rag, static_rag, chat, reports

logger = logging.getLogger(__name__)

_sql_rag_chain = None
_static_rag_chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    global _sql_rag_chain
    
    logger.info("Starting up DualRAG API server...")
    
    try:
        config = Config.from_file(".env")
        db_connection = config.get("database.connection_string")
        
        if not db_connection:
            logger.warning("No database connection string configured. SQL RAG disabled.")
            _sql_rag_chain = None
        else:
            logger.info("Initializing SQL RAG Chain...")
            _sql_rag_chain = SQLRAGChain(connection_string=db_connection)
            sql_rag.set_sql_rag_chain(_sql_rag_chain)
            logger.info("SQL RAG Chain initialized successfully")
    
    except Exception as e:
        logger.error(f"Failed to initialize SQL RAG Chain: {e}")
        _sql_rag_chain = None
    
    try:
        logger.info("Initializing Static RAG Chain...")
        _static_rag_chain = StaticRAGChain()
        static_rag.set_static_rag_chain(_static_rag_chain)
        logger.info("Static RAG Chain initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Static RAG Chain: {e}")
        _static_rag_chain = None
    
    yield
    
    logger.info("Shutting down DualRAG API server...")
    if _sql_rag_chain:
        try:
            _sql_rag_chain.close()
            logger.info("SQL RAG Chain closed")
        except Exception as e:
            logger.error(f"Error closing SQL RAG Chain: {e}")
    if _static_rag_chain:
        try:
            if hasattr(_static_rag_chain, 'close'):
                _static_rag_chain.close()
            logger.info("Static RAG Chain closed")
        except Exception as e:
            logger.error(f"Error closing Static RAG Chain: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="DualRAG Chatbot API",
        description="Advanced RAG system combining static and SQL-based knowledge retrieval",
        version="1.0.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.middleware("http")(error_handler_middleware)
    app.middleware("http")(logging_middleware)
    
    app.include_router(health.router)
    app.include_router(sql_rag.router)
    app.include_router(static_rag.router)
    app.include_router(chat.router)
    app.include_router(reports.router)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "DualRAG Chatbot API",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "operational"
        }
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info"
    )
