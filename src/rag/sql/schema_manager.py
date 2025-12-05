"""
Database Schema Management and Caching.

Manages schema versioning, lazy loading, and caching for SQL RAG.
Handles schema retrieval, updates, and provides schema context for LLM.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.rag.sql.connector import SQLConnector
from src.schemas.sql import SchemaTable, DatabaseSchema
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class SchemaManager:
    """
    Database schema manager with caching, versioning, and lazy loading.
    
    Features:
    - Schema caching with TTL
    - Schema versioning for change tracking
    - Lazy loading of table details
    - Relationship mapping (foreign keys)
    - Schema summary generation for LLM context
    - Refresh and invalidation controls
    """
    
    def __init__(
        self,
        connector: SQLConnector,
        cache_ttl: int = 3600,  # 1 hour
        enable_versioning: bool = True
    ):
        """
        Initialize schema manager.
        
        Args:
            connector: SQLConnector instance for database access
            cache_ttl: Cache TTL in seconds (default 1 hour)
            enable_versioning: Enable schema versioning
        """
        self.connector = connector
        self.cache_ttl = cache_ttl
        self.enable_versioning = enable_versioning
        
        # Caching
        self._schema_cache: Optional[DatabaseSchema] = None
        self._cache_time = 0
        self._cache_valid = False
        
        # Versioning
        self._schema_versions: List[Dict[str, Any]] = []
        self._current_version = 0
        
        # Lazy loading
        self._tables_loaded = {}  # table_name -> detailed schema
    
    def get_schema(self, use_cache: bool = True, refresh: bool = False) -> DatabaseSchema:
        """
        Get complete database schema.
        
        Args:
            use_cache: Use cached schema if available and valid
            refresh: Force refresh from database
        
        Returns:
            DatabaseSchema with all tables and relationships
        """
        # Check cache validity
        if use_cache and not refresh:
            if self._is_cache_valid():
                logger.debug("Using cached database schema")
                return self._schema_cache
        
        logger.info("Fetching database schema from connector...")
        
        # Get raw schema from connector
        raw_schema = self.connector.get_schema(use_cache=False)
        
        # Parse into SchemaTable objects
        tables = []
        for table_name, table_info in raw_schema.get('tables', {}).items():
            columns = [col['name'] for col in table_info.get('columns', [])]
            column_types = {
                col['name']: col['type'] 
                for col in table_info.get('columns', [])
            }
            
            table = SchemaTable(
                table_name=table_name,
                columns=columns,
                column_types=column_types,
                primary_key=self._find_primary_key(table_name),
                sample_rows=len(columns)  # Placeholder
            )
            tables.append(table)
        
        # Get relationships
        relationships = self._get_relationships()
        
        # Create DatabaseSchema
        schema = DatabaseSchema(
            database_name=self.connector.database,
            tables=tables,
            relationships=relationships,
            last_updated=datetime.now()
        )
        
        # Cache schema
        self._schema_cache = schema
        self._cache_time = time.time()
        self._cache_valid = True
        
        # Track version if enabled
        if self.enable_versioning:
            self._track_version(schema)
        
        logger.info(f"Schema loaded: {len(tables)} tables")
        return schema
    
    def get_table_schema(self, table_name: str, lazy_load: bool = True) -> Optional[SchemaTable]:
        """
        Get schema for a specific table with optional lazy loading.
        
        Args:
            table_name: Name of the table
            lazy_load: If True, cache table details for subsequent calls
        
        Returns:
            SchemaTable or None if table not found
        """
        # Check lazy loaded cache
        if lazy_load and table_name in self._tables_loaded:
            logger.debug(f"Using cached table schema: {table_name}")
            return self._tables_loaded[table_name]
        
        # Get from full schema
        schema = self.get_schema()
        table = next((t for t in schema.tables if t.table_name == table_name), None)
        
        # Cache if lazy loading enabled
        if lazy_load and table:
            self._tables_loaded[table_name] = table
            logger.debug(f"Cached table schema: {table_name}")
        
        return table
    
    def get_schema_summary(self, include_descriptions: bool = False) -> str:
        """
        Generate human-readable schema summary for LLM context.
        
        Args:
            include_descriptions: Include column descriptions if available
        
        Returns:
            Formatted schema summary string
        """
        schema = self.get_schema()
        
        summary_lines = [f"Database: {schema.database_name}\n"]
        
        # Tables
        summary_lines.append("Tables:")
        for table in schema.tables:
            cols_str = ", ".join(table.columns)
            pk_str = f" (PK: {table.primary_key})" if table.primary_key else ""
            summary_lines.append(f"  - {table.table_name}({cols_str}){pk_str}")
        
        # Relationships
        if schema.relationships:
            summary_lines.append("\nRelationships:")
            for source, targets in schema.relationships.items():
                for target in targets:
                    summary_lines.append(f"  - {source} -> {target}")
        
        return "\n".join(summary_lines)
    
    def get_schema_context(self, max_length: int = 2000) -> str:
        """
        Get concise schema context for LLM query generation.
        
        Args:
            max_length: Maximum length of context string
        
        Returns:
            Concise schema context suitable for LLM
        """
        schema = self.get_schema()
        
        context = f"Database: {schema.database_name}\n\n"
        context += "Tables and columns:\n"
        
        for table in schema.tables:
            line = f"{table.table_name}: {', '.join(table.columns)}\n"
            if len(context) + len(line) > max_length:
                context += "... (truncated)"
                break
            context += line
        
        return context
    
    def refresh_schema(self, invalidate_all: bool = False) -> DatabaseSchema:
        """
        Refresh schema from database.
        
        Args:
            invalidate_all: If True, also clear lazy-loaded table cache
        
        Returns:
            Updated DatabaseSchema
        """
        logger.info("Refreshing database schema...")
        
        if invalidate_all:
            self._tables_loaded.clear()
        
        return self.get_schema(use_cache=False, refresh=True)
    
    def invalidate_cache(self) -> None:
        """Invalidate schema cache to force refresh on next access."""
        self._cache_valid = False
        self._tables_loaded.clear()
        logger.info("Schema cache invalidated")
    
    def get_schema_version(self) -> int:
        """Get current schema version number."""
        return self._current_version
    
    def get_schema_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get schema version history.
        
        Args:
            limit: Maximum versions to return
        
        Returns:
            List of version records
        """
        return self._schema_versions[-limit:]
    
    def _is_cache_valid(self) -> bool:
        """Check if cached schema is still valid."""
        if not self._cache_valid or not self._schema_cache:
            return False
        
        cache_age = time.time() - self._cache_time
        if cache_age > self.cache_ttl:
            logger.debug(f"Schema cache expired (age: {cache_age:.0f}s)")
            self._cache_valid = False
            return False
        
        return True
    
    def _find_primary_key(self, table_name: str) -> Optional[str]:
        """
        Find primary key for a table.
        
        Args:
            table_name: Table name
        
        Returns:
            Primary key column name or None
        """
        # Simple heuristic: look for 'id' column
        # In production, query information_schema
        query = f"""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid
            AND a.attnum = ANY(i.indkey)
        WHERE i.indrelname = '{table_name}_pkey'
        LIMIT 1
        """
        
        try:
            result = self.connector.execute_query(query)
            if result['status'] == 'success' and result['rows']:
                return result['rows'][0].get('attname')
        except Exception as e:
            logger.debug(f"Could not find primary key for {table_name}: {e}")
        
        return None
    
    def _get_relationships(self) -> Dict[str, List[str]]:
        """
        Get foreign key relationships.
        
        Returns:
            Dict of foreign key relationships
        """
        query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        """
        
        relationships = {}
        
        try:
            result = self.connector.execute_query(query)
            if result['status'] == 'success':
                for row in result['rows']:
                    source = f"{row['table_name']}.{row['column_name']}"
                    target = f"{row['foreign_table_name']}.{row['foreign_column_name']}"
                    
                    if source not in relationships:
                        relationships[source] = []
                    relationships[source].append(target)
        except Exception as e:
            logger.warning(f"Could not retrieve relationships: {e}")
        
        return relationships
    
    def _track_version(self, schema: DatabaseSchema) -> None:
        """Track schema version for change tracking."""
        version_record = {
            "version": self._current_version,
            "timestamp": datetime.now(),
            "table_count": len(schema.tables),
            "tables": [t.table_name for t in schema.tables]
        }
        
        self._schema_versions.append(version_record)
        self._current_version += 1
        
        # Keep only last 10 versions
        if len(self._schema_versions) > 10:
            self._schema_versions = self._schema_versions[-10:]
        
        logger.debug(f"Tracked schema version {self._current_version}")

