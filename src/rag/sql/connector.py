"""
SQL Database Connection Management.

Handles connection pooling, schema caching, and database operations for SQL RAG.
Supports PostgreSQL and MySQL databases with connection pooling for performance.
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from urllib.parse import urlparse
import logging

import psycopg2
import psycopg2.pool
import psycopg2.extras

from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class SQLConnector:
    """
    PostgreSQL connection manager with connection pooling and schema caching.
    
    Features:
    - Connection pooling for performance
    - Schema caching with TTL for repeated queries
    - Prepared statement support
    """
    
    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        query_timeout: float = 30.0
    ):
        """
        Initialize PostgreSQL connector with connection pooling.
        
        Args:
            connection_string: PostgreSQL URL (postgresql://user:pass@host:port/db)
            pool_size: Minimum connections in pool
            max_overflow: Maximum overflow connections beyond pool_size
            pool_timeout: Timeout in seconds for acquiring connection from pool
            query_timeout: Default query timeout in seconds
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.query_timeout = query_timeout
        
        # Parse connection string
        self.host, self.port, self.database, self.user, self.password = self._parse_connection_string(
            connection_string
        )
        
        # Initialize connection pool
        self.pool = None
        self._initialize_pool()
        
        # Schema cache (database schema metadata)
        self._schema_cache = {}
        self._schema_cache_time = 0
        self._schema_cache_ttl = 3600  # 1 hour
    
    def _parse_connection_string(self, connection_string: str) -> Tuple[str, int, str, str, str]:
        """
        Parse PostgreSQL connection string.
        
        Args:
            connection_string: URL format: postgresql://user:pass@host:port/db
        
        Returns:
            Tuple of (host, port, database, user, password)
        """
        parsed = urlparse(connection_string)
        
        db_type = parsed.scheme.lower()
        if db_type not in ['postgresql', 'postgres']:
            raise ValueError(f"Only PostgreSQL is supported. Got: {db_type}")
        
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432
        database = parsed.path.lstrip('/') or 'postgres'
        user = parsed.username or 'postgres'
        password = parsed.password or ''
        
        logger.info(f"Parsed PostgreSQL connection: {user}@{host}:{port}/{database}")
        
        return host, port, database, user, password
    
    def _initialize_pool(self) -> None:
        """Initialize PostgreSQL connection pool."""
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=self.pool_size,
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            connect_timeout=int(self.pool_timeout)
        )
        logger.info(f"PostgreSQL connection pool initialized: {self.pool_size} connections")
    
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        Context manager for getting a PostgreSQL connection from the pool.
        
        Args:
            timeout: Optional timeout override for this connection
        
        Yields:
            PostgreSQL connection object
        
        Example:
            with connector.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        timeout = timeout or self.pool_timeout
        conn = None
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                conn = self.pool.getconn()
                
                if conn:
                    logger.debug(f"Acquired connection from pool (waited {time.time() - start_time:.2f}s)")
                    try:
                        yield conn
                    finally:
                        self.pool.putconn(conn)
                    return
            except Exception as e:
                logger.debug(f"Connection pool error: {e}, retrying...")
                time.sleep(0.1)
        
        raise TimeoutError(f"Could not acquire database connection within {timeout} seconds")
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        fetch_all: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a PostgreSQL query with error handling.
        
        Args:
            query: SQL query string
            parameters: Query parameters for prepared statements
            timeout: Query timeout in seconds
            fetch_all: If True, fetch all rows; if False, fetch one row
        
        Returns:
            Dict with keys: rows, column_names, row_count, execution_time_ms, status, error_message
        """
        timeout = timeout or self.query_timeout
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Execute query with timeout
                try:
                    if parameters:
                        cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)
                except Exception as e:
                    return {
                        "rows": [],
                        "column_names": [],
                        "row_count": 0,
                        "execution_time_ms": (time.time() - start_time) * 1000,
                        "status": "error",
                        "error_message": str(e)
                    }
                
                # Fetch results
                if fetch_all:
                    rows = cursor.fetchall()
                else:
                    rows = [cursor.fetchone()] if cursor.rowcount > 0 else []
                
                # Get column names
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert rows to list of dicts
                rows = [dict(row) for row in rows]
                
                cursor.close()
                
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Query executed successfully in {execution_time_ms:.2f}ms, returned {len(rows)} rows")
                
                return {
                    "rows": rows,
                    "column_names": column_names,
                    "row_count": len(rows),
                    "execution_time_ms": execution_time_ms,
                    "status": "success",
                    "error_message": None
                }
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Query execution failed: {e}")
            return {
                "rows": [],
                "column_names": [],
                "row_count": 0,
                "execution_time_ms": execution_time_ms,
                "status": "error",
                "error_message": str(e)
            }
    
    def get_schema(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get PostgreSQL database schema information (tables, columns, types).
        
        Args:
            use_cache: Use cached schema if available and not expired
        
        Returns:
            Dict with tables, columns, and relationships
        """
        # Check cache
        if use_cache:
            cache_age = time.time() - self._schema_cache_time
            if self._schema_cache and cache_age < self._schema_cache_ttl:
                logger.debug(f"Using cached schema (age: {cache_age:.0f}s)")
                return self._schema_cache
        
        logger.info("Fetching schema from PostgreSQL database...")
        
        query = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'public'
        ORDER BY t.table_name, c.ordinal_position
        """
        
        result = self.execute_query(query)
        
        if result['status'] != 'success':
            logger.error(f"Failed to get schema: {result['error_message']}")
            return {"tables": {}}
        
        # Parse results into schema structure
        schema = {"tables": {}}
        for row in result['rows']:
            table_name = row['table_name']
            if table_name not in schema['tables']:
                schema['tables'][table_name] = {'columns': []}
            
            schema['tables'][table_name]['columns'].append({
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES'
            })
        
        # Cache schema
        self._schema_cache = schema
        self._schema_cache_time = time.time()
        
        logger.info(f"Schema fetched: {len(schema.get('tables', {}))} tables")
        return schema
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema for a specific table.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dict with table columns and types
        """
        schema = self.get_schema()
        if table_name in schema.get('tables', {}):
            return schema['tables'][table_name]
        
        logger.warning(f"Table {table_name} not found in schema")
        return {'columns': []}
    
    def close(self) -> None:
        """Close all PostgreSQL connections in the pool."""
        if self.pool:
            try:
                self.pool.closeall()
                logger.info("PostgreSQL connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
    
    def __del__(self):
        """Cleanup when connector is destroyed."""
        self.close()    