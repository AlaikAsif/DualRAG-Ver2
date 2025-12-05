"""
Database Schema Retrieval and Semantic Search.

Retrieves relevant schema information based on query context.
Performs semantic matching of tables and columns to natural language queries.
"""

from typing import List, Dict, Any, Optional
from src.rag.sql.schema_manager import SchemaManager
from src.schemas.sql import SchemaTable, DatabaseSchema
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class SchemaRetriever:
    """
    Retrieves relevant database schema based on query context.
    
    Features:
    - Retrieve all tables and columns
    - Semantic search for relevant tables
    - Column information retrieval
    - Relationship information
    - Schema filtering by keywords
    """
    
    def __init__(self, schema_manager: SchemaManager):
        """
        Initialize schema retriever.
        
        Args:
            schema_manager: SchemaManager instance for schema access
        """
        self.schema_manager = schema_manager
    
    def get_all_tables(self) -> List[str]:
        """Get names of all tables in database."""
        schema = self.schema_manager.get_schema()
        return [table.table_name for table in schema.tables]
    
    def get_all_columns(self) -> Dict[str, List[str]]:
        """
        Get all columns grouped by table.
        
        Returns:
            Dict mapping table names to column lists
        """
        schema = self.schema_manager.get_schema()
        return {
            table.table_name: table.columns 
            for table in schema.tables
        }
    
    def find_relevant_tables(
        self,
        query: str,
        threshold: float = 0.3,
        max_tables: int = 5
    ) -> List[SchemaTable]:
        """
        Find relevant tables for a natural language query using keyword matching.
        
        Args:
            query: Natural language query
            threshold: Keyword match threshold (0-1)
            max_tables: Maximum tables to return
        
        Returns:
            List of relevant SchemaTable objects
        """
        schema = self.schema_manager.get_schema()
        query_keywords = set(query.lower().split())
        
        # Score tables by keyword match
        scored_tables = []
        for table in schema.tables:
            # Score table name match
            table_name_match = sum(
                1 for keyword in query_keywords 
                if keyword in table.table_name.lower()
            )
            
            # Score column name match
            column_matches = sum(
                1 for col in table.columns 
                for keyword in query_keywords 
                if keyword in col.lower()
            )
            
            total_score = (table_name_match * 2 + column_matches) / (len(query_keywords) + 1)
            
            if total_score >= threshold:
                scored_tables.append((table, total_score))
        
        # Sort by score and return top results
        scored_tables.sort(key=lambda x: x[1], reverse=True)
        relevant_tables = [table for table, _ in scored_tables[:max_tables]]
        
        logger.info(f"Found {len(relevant_tables)} relevant tables for query")
        return relevant_tables
    
    def get_table_info(self, table_name: str) -> Optional[SchemaTable]:
        return self.schema_manager.get_table_schema(table_name)
    
    def get_table_columns(self, table_name: str) -> Optional[Dict[str, str]]:
        table = self.schema_manager.get_table_schema(table_name)
        if table:
            return table.column_types
        return None
    
    def get_relationships(self) -> Dict[str, List[str]]:
        #Get foreign key relationships.
        schema = self.schema_manager.get_schema()
        return schema.relationships
    
    def get_schema_context(self, relevant_tables: Optional[List[str]] = None) -> str:
        """
        Generate schema context string for LLM.
        
        Args:
            relevant_tables: If provided, only include these tables
        
        Returns:
            Formatted schema context string
        """
        schema = self.schema_manager.get_schema()
        
        context_lines = []
        
        for table in schema.tables:
            # Filter tables if specified
            if relevant_tables and table.table_name not in relevant_tables:
                continue
            
            # Format table with columns
            columns_str = ", ".join(
                f"{col} ({table.column_types.get(col, 'UNKNOWN')})"
                for col in table.columns
            )
            pk_str = f" [PK: {table.primary_key}]" if table.primary_key else ""
            context_lines.append(f"{table.table_name}: {columns_str}{pk_str}")
        
        return "\n".join(context_lines)

