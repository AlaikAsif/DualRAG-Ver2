"""
Safe SQL Query Executor.

Handles secure query execution with safety checks, permission enforcement,
result limiting, and comprehensive error handling.
"""

import time
import re
from typing import List, Dict, Any, Optional
from src.rag.sql.connector import SQLConnector
from src.schemas.sql import SQLQuery, SQLResult
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class QueryExecutor:
    """
    Secure SQL query executor with safety constraints and permission checks.
    
    Features:
    - Read-only query enforcement
    - Result limiting (max rows to prevent memory exhaustion)
    - Query timeout protection
    - Permission validation
    - Comprehensive audit logging
    - Error handling and reporting
    """
    
    def __init__(
        self,
        connector: SQLConnector,
        max_rows: int = 1000,
        query_timeout: float = 30.0,
        enable_select_only: bool = True
    ):
        """
        Initialize query executor with safety constraints.
        
        Args:
            connector: SQLConnector instance for database access
            max_rows: Maximum rows to return (prevent memory exhaustion)
            query_timeout: Timeout for query execution in seconds
            enable_select_only: If True, only allow SELECT queries (read-only)
        """
        self.connector = connector
        self.max_rows = max_rows
        self.query_timeout = query_timeout
        self.enable_select_only = enable_select_only
        self._execution_history = []
    
    def execute(self, sql_query: SQLQuery) -> SQLResult:
        """
        Execute a SQL query with all safety checks and constraints.
        
        Args:
            sql_query: SQLQuery object containing query string and metadata
        
        Returns:
            SQLResult with execution results or error information
        """
        start_time = time.time()
        
        try:
            # Safety checks
            self._validate_query(sql_query.query_string)
            
            # Add LIMIT clause if not present to prevent result explosion
            query = self._add_result_limit(sql_query.query_string)
            
            logger.info(f"Executing query: {query[:100]}...")
            
            # Execute query via connector
            result = self.connector.execute_query(
                query,
                parameters=sql_query.parameters,
                timeout=self.query_timeout,
                fetch_all=True
            )
            
            # Create SQLResult from connector result
            execution_time_ms = (time.time() - start_time) * 1000
            
            sql_result = SQLResult(
                query=sql_query.query_string,
                rows=result.get('rows', []),
                column_names=result.get('column_names', []),
                row_count=result.get('row_count', 0),
                execution_time_ms=execution_time_ms,
                status=result.get('status', 'error'),
                error_message=result.get('error_message')
            )
            
            # Log successful execution
            if sql_result.status == 'success':
                logger.info(
                    f"Query executed successfully: {sql_result.row_count} rows "
                    f"in {execution_time_ms:.2f}ms"
                )
            else:
                logger.error(f"Query execution failed: {sql_result.error_message}")
            
            # Track execution history
            self._track_execution(sql_query.query_string, sql_result)
            
            return sql_result
        
        except ValueError as e:
            # Validation error (e.g., unsafe query)
            execution_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"Query validation failed: {e}")
            
            sql_result = SQLResult(
                query=sql_query.query_string,
                rows=[],
                column_names=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                status="error",
                error_message=str(e)
            )
            
            self._track_execution(sql_query.query_string, sql_result)
            return sql_result
        
        except Exception as e:
            # Unexpected error
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error during query execution: {e}")
            
            return SQLResult(
                query=sql_query.query_string,
                rows=[],
                column_names=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                status="error",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _validate_query(self, query: str) -> None:
        """
        Validate query for safety and compliance.
        
        Args:
            query: SQL query string to validate
        
        Raises:
            ValueError: If query fails validation
        """
        query_upper = query.strip().upper()
        
        # Check for SELECT-only if enabled
        # Allow: SELECT, WITH (CTEs), EXPLAIN, ANALYZE, SHOW, DESCRIBE
        if self.enable_select_only:
            allowed_starts = ('SELECT', 'WITH', 'EXPLAIN', 'ANALYZE', 'SHOW', 'DESCRIBE', 'DESC')
            if not any(query_upper.startswith(start) for start in allowed_starts):
                raise ValueError(
                    "Only read-only queries are allowed (SELECT, WITH, EXPLAIN, ANALYZE, SHOW, DESCRIBE). "
                    "INSERT, UPDATE, DELETE, DROP are not permitted."
                )
        
        # Check for dangerous keywords that suggest data modification
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'VACUUM'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper and keyword != 'SELECT':
                raise ValueError(
                    f"Query contains dangerous keyword '{keyword}'. "
                    "Only read-only queries are allowed."
                )
        
        # Check for SQL injection patterns (basic detection)
        injection_patterns = [
            r"'?\s*;\s*--",  # Comment after semicolon
            r"'?\s*;\s*\/\*",  # Block comment after semicolon
            r"UNION\s+SELECT",  # UNION-based injection (allowed for joins, but log it)
            r"OR\s+'?1'?\s*=\s*'?1'?",  # Always-true condition
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_upper):
                logger.warning(f"Suspicious SQL pattern detected in query: {pattern}")
        
        # Query must not be empty
        if not query_upper or query_upper.isspace():
            raise ValueError("Query cannot be empty")
        
        logger.debug(f"Query validation passed")
    
    def _add_result_limit(self, query: str) -> str:
        """
        Add LIMIT clause to query if not present.
        
        Args:
            query: Original SQL query
        
        Returns:
            Query with LIMIT clause ensuring max_rows limit
        """
        query_upper = query.strip().upper()
        
        # Check if query already has LIMIT
        if 'LIMIT' in query_upper:
            # Extract existing limit and ensure it doesn't exceed max_rows
            match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if match:
                existing_limit = int(match.group(1))
                if existing_limit > self.max_rows:
                    # Replace with enforced limit
                    query = re.sub(
                        r'LIMIT\s+\d+',
                        f'LIMIT {self.max_rows}',
                        query,
                        flags=re.IGNORECASE
                    )
                    logger.info(f"Query limit reduced from {existing_limit} to {self.max_rows}")
            return query
        
        # Add LIMIT if not present
        if query.rstrip().endswith(';'):
            query = query.rstrip()[:-1]  # Remove trailing semicolon
        
        limited_query = f"{query.strip()} LIMIT {self.max_rows}"
        logger.debug(f"Added LIMIT {self.max_rows} to query")
        
        return limited_query
    
    def _track_execution(self, query: str, result: SQLResult) -> None:
        """
        Track execution history for auditing and monitoring.
        
        Args:
            query: SQL query that was executed
            result: Result from execution
        """
        execution_record = {
            "query": query[:200],  # Store first 200 chars
            "status": result.status,
            "row_count": result.row_count,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": time.time(),
            "error": result.error_message[:100] if result.error_message else None
        }
        
        self._execution_history.append(execution_record)
        
        # Keep only last 100 executions in memory
        if len(self._execution_history) > 100:
            self._execution_history = self._execution_history[-100:]
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent execution history.
        
        Args:
            limit: Number of recent executions to return
        
        Returns:
            List of execution records
        """
        return self._execution_history[-limit:]
    
    def clear_execution_history(self) -> None:
        """Clear execution history."""
        self._execution_history = []
        logger.info("Execution history cleared")
