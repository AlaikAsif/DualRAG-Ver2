"""
SQL RAG Chain: Natural language to SQL query generation and execution.

This chain converts natural language questions into SQL queries, validates them for safety,
executes them against the database, and formats results for the LLM. Integrates with database
connector, schema management, query generation, validation, and result parsing.
"""

from typing import Optional, Dict, Any, List, Tuple
import time

from src.rag.sql.connector import SQLConnector
from src.rag.sql.schema_manager import SchemaManager
from src.rag.sql.schema_retriever import SchemaRetriever
from src.rag.sql.schema_embeddings import SchemaEmbeddings
from src.rag.sql.query_generator import QueryGenerator
from src.rag.sql.validator import QueryValidator
from src.rag.sql.executor import QueryExecutor
from src.rag.sql.result_parser import ResultParser
from src.rag.static.embeddings import StaticEmbeddings
from src.chains.llm import LLM
from src.schemas.sql import (
    SQLQuery, SQLResult, SQLRagRequest, SQLRagResponse
)
from src.monitoring.logger import get_logger
from src.monitoring.tracer import trace_chain_execution
from src.utils.config import get_config
from src.utils.retry import retry_with_backoff
from datetime import datetime

logger = get_logger(__name__)
config = get_config()


class SQLRAGChain:
    """
    SQL RAG Chain for natural language to database query pipeline.
    
    Workflow:
    1. Retrieve relevant schema elements based on natural language query
    2. Generate SQL query using LLM with schema context
    3. Validate query for safety and correctness
    4. Execute query against database with safety constraints
    5. Parse and format results for LLM consumption
    
    Features:
    - Multi-stage query validation (syntax, schema, safety)
    - Confidence scoring for generated queries
    - Automatic retry on invalid queries
    - Result formatting for LLM responses
    - Comprehensive error handling and logging
    
    Attributes:
        connector (SQLConnector): Database connection pool manager
        schema_manager (SchemaManager): Schema versioning and management
        schema_retriever (SchemaRetriever): Keyword-based schema search
        schema_embeddings (SchemaEmbeddings): Vector-based semantic search
        query_generator (QueryGenerator): LLM-based SQL generation
        validator (QueryValidator): Query validation pipeline
        executor (QueryExecutor): Safe query execution
        result_parser (ResultParser): Result formatting
        llm (LLM): Language model for query generation
        max_retries (int): Max retry attempts on failed queries
        confidence_threshold (float): Min confidence score (0-1)
    """
    
    def __init__(
        self,
        connection_string: str,
        llm: Optional[LLM] = None,
        max_retries: int = 2,
        confidence_threshold: float = 0.5,
        pool_size: int = 5,
        query_timeout: float = 30.0,
        result_limit: int = 1000,
        enable_embeddings: bool = True
    ):
        """
        Initialize SQL RAG Chain.
        
        Args:
            connection_string: PostgreSQL connection URL
            llm: Language model instance (uses default if None)
            max_retries: Max retry attempts on invalid queries
            confidence_threshold: Min confidence score for accepting query (0-1)
            pool_size: Database connection pool size
            query_timeout: Query execution timeout in seconds
            result_limit: Max rows to return from query
            enable_embeddings: Use semantic search with embeddings
        """
        logger.info("Initializing SQL RAG Chain...")
        
        self.connector = SQLConnector(
            connection_string=connection_string,
            pool_size=pool_size,
            query_timeout=query_timeout
        )
        self.schema_manager = SchemaManager(self.connector)
        
        self.schema_retriever = SchemaRetriever(self.schema_manager)
        
        self.enable_embeddings = enable_embeddings
        if enable_embeddings:
            embedding_model = StaticEmbeddings()
            self.schema_embeddings = SchemaEmbeddings(
                schema_manager=self.schema_manager,
                embedding_model=embedding_model,
                cache_embeddings=True
            )
        else:
            self.schema_embeddings = None
        
        self.llm = llm or LLM()
        self.query_generator = QueryGenerator(
            llm_client=self.llm,
            schema_retriever=self.schema_retriever,
            schema_embeddings=self.schema_embeddings if enable_embeddings else None
        )
        
        self.validator = QueryValidator(self.schema_manager)
        self.executor = QueryExecutor(
            self.connector,
            max_rows=result_limit,
            query_timeout=query_timeout
        )
        
        self.result_parser = ResultParser()
        
        self.max_retries = max_retries
        self.confidence_threshold = confidence_threshold
        self.result_limit = result_limit
        
        logger.info("SQL RAG Chain initialized successfully")
    
    @trace_chain_execution(chain_name="SQLRAGChain.process")
    def process(
        self,
        request: SQLRagRequest,
        use_context: bool = True
    ) -> SQLRagResponse:
        """
        Process natural language request to SQL response.
        
        Pipeline:
        1. Retrieve relevant schema elements
        2. Generate SQL with schema context
        3. Validate for safety and correctness
        4. Execute against database
        5. Format results for LLM
        
        Args:
            request: SQL RAG request with natural language query
            use_context: Include schema context in generation
        
        Returns:
            SQLRagResponse with generated query, results, and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing SQL RAG request: {request.query[:100]}...")
            
            logger.debug("Retrieving relevant schema...")
            relevant_tables = self.schema_retriever.find_relevant_tables(
                request.query,
                threshold=0.3,
                max_tables=5
            )
            logger.info(f"Found {len(relevant_tables)} relevant tables")
            
            schema_context = self.schema_retriever.get_schema_context(relevant_tables)
            
            logger.debug("Generating SQL query...")
            generated_query, explanation, confidence = self._generate_query_with_retry(
                request.query,
                schema_context,
                request.previous_queries
            )
            
            if not generated_query:
                return SQLRagResponse(
                    original_query=request.query,
                    generated_sql="",
                    sql_explanation="Could not generate valid SQL query after retries",
                    query_result=SQLResult(query="", status="failed"),
                    interpretation="Query generation failed",
                    confidence=0.0
                )
            
            logger.info(
                f"Generated query with confidence={confidence:.2f}: {generated_query.query_string[:100]}..."
            )
            
            logger.debug("Validating query...")
            is_valid, validation_errors = self.validator.validate(generated_query)
            
            if not is_valid:
                return SQLRagResponse(
                    original_query=request.query,
                    generated_sql=generated_query.query_string,
                    sql_explanation=explanation,
                    query_result=SQLResult(query=generated_query.query_string, status="validation_failed"),
                    interpretation=f"Query validation failed: {validation_errors}",
                    confidence=confidence
                )
            
            logger.info("Query validation passed")
            
            logger.debug("Executing query...")
            result = self.executor.execute(generated_query)
            
            logger.info(
                f"Query executed: {result.row_count} rows in {result.execution_time_ms:.2f}ms"
            )
            
            logger.debug("Formatting results...")
            formatted_result = self.result_parser.format_for_llm(result)
            
            execution_time = time.time() - start_time
            
            return SQLRagResponse(
                original_query=request.query,
                generated_sql=generated_query.query_string,
                sql_explanation=explanation,
                query_result=result,
                interpretation=formatted_result,
                confidence=confidence,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"SQL RAG chain error: {e}", exc_info=True)
            
            return SQLRagResponse(
                original_query=request.query,
                generated_sql="",
                sql_explanation=str(e),
                query_result=SQLResult(query="", status="error", error_message=str(e)),
                interpretation=f"Error: {str(e)}",
                confidence=0.0
            )
    
    def _generate_query_with_retry(
        self,
        natural_query: str,
        schema_context: str,
        previous_queries: List[str] = None
    ) -> Tuple[Optional[SQLQuery], str, float]:
        """
        Generate SQL query with retry logic on validation failure.
        
        Args:
            natural_query: Natural language question
            schema_context: Relevant schema information
            previous_queries: Previous successful queries for context
        
        Returns:
            Tuple of (SQLQuery, explanation, confidence) or (None, "", 0) on failure
        """
        previous_queries = previous_queries or []
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Query generation attempt {attempt + 1}/{self.max_retries + 1}")
                
                request = SQLRagRequest(
                    query=natural_query,
                    database_context=schema_context,
                    previous_queries=previous_queries
                )
                
                sql_query, explanation, confidence = self.query_generator.generate(request)
                
                logger.debug(f"Generated query with confidence={confidence:.2f}")
                
                if confidence >= self.confidence_threshold:
                    return sql_query, explanation, confidence
                
                is_valid, _ = self.validator.validate(sql_query)
                if is_valid:
                    logger.info(f"Accepting query despite low confidence ({confidence:.2f})")
                    return sql_query, explanation, confidence
                
                logger.warning(f"Query generation produced invalid query, retrying...")
                
            except Exception as e:
                logger.warning(f"Query generation error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Query generation failed after {self.max_retries + 1} attempts")
                    return None, "", 0.0
        
        return None, "", 0.0
    
    def close(self) -> None:
        """Close database connections."""
        try:
            self.connector.close()
            logger.info("SQL RAG Chain connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_schema_summary(self) -> str:
        """
        Get human-readable schema summary.
        
        Returns:
            Formatted schema summary
        """
        return self.schema_manager.get_schema_summary()
    
    def refresh_schema(self) -> None:
        """Refresh cached schema from database."""
        logger.info("Refreshing schema cache...")
        self.schema_manager.refresh_schema()
        logger.info("Schema cache refreshed")
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent query execution history.
        
        Args:
            limit: Max number of entries to return
        
        Returns:
            List of execution history entries
        """
        return self.executor.get_execution_history(limit)
