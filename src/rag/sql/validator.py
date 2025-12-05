"""
SQL Query Validation and Safety Checks.

Validates generated SQL queries for safety, correctness, and schema compatibility.
"""

import re
from typing import List, Tuple, Optional
from src.rag.sql.schema_manager import SchemaManager
from src.schemas.sql import SQLQuery
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class QueryValidator:
    """
    Validate generated SQL queries.
    
    Features:
    - SQL syntax validation
    - Schema compatibility checks
    - SQL injection detection
    - Query safety checks
    """
    
    def __init__(self, schema_manager: SchemaManager):
        """
        Initialize validator.
        
        Args:
            schema_manager: SchemaManager for schema context
        """
        self.schema_manager = schema_manager
    
    def validate(self, sql_query: SQLQuery) -> Tuple[bool, List[str]]:
        """
        Validate SQL query completely.
        
        Args:
            sql_query: SQLQuery to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Run all validation checks
        errors.extend(self._validate_syntax(sql_query.query_string))
        errors.extend(self._validate_schema_compatibility(sql_query.query_string))
        errors.extend(self._validate_safety(sql_query.query_string))
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Query validation passed")
        else:
            logger.warning(f"Query validation failed with {len(errors)} errors")
        
        return is_valid, errors
    
    def _validate_syntax(self, query: str) -> List[str]:
        """Validate basic SQL syntax."""
        errors = []
        
        query_upper = query.strip().upper()
        
        # Check for empty query
        if not query.strip():
            errors.append("Query cannot be empty")
            return errors
        
        # Check for valid SQL start
        valid_starts = ('SELECT', 'WITH')
        if not any(query_upper.startswith(start) for start in valid_starts):
            errors.append(f"Query must start with SELECT or WITH, got: {query[:20]}")
        
        # Check for balanced parentheses
        if query.count('(') != query.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for unmatched quotes
        single_quotes = query.count("'") - query.count("\\'")
        if single_quotes % 2 != 0:
            errors.append("Unmatched single quotes")
        
        # Check for suspicious semicolons (multiple statements)
        if query.count(';') > 1:
            errors.append("Multiple SQL statements not allowed")
        
        return errors
    
    def _validate_schema_compatibility(self, query: str) -> List[str]:
        """Validate query against database schema."""
        errors = []
        
        schema = self.schema_manager.get_schema()
        available_tables = {t.table_name.lower(): t for t in schema.tables}
        available_columns = {}
        
        # Build available columns map
        for table in schema.tables:
            for col in table.columns:
                col_key = f"{table.table_name.lower()}.{col.lower()}"
                available_columns[col_key] = (table.table_name, col)
        
        query_upper = query.upper()
        
        # Extract table names from FROM/JOIN clauses
        from_tables = self._extract_tables(query)
        
        for table_name in from_tables:
            if table_name.lower() not in available_tables:
                errors.append(f"Table '{table_name}' not found in schema")
        
        # Extract column references (simplified)
        # Look for SELECT ... FROM pattern
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query_upper)
        if select_match:
            select_clause = select_match.group(1)
            # Check for * (all columns)
            if select_clause.strip() != '*':
                # Extract column names
                columns = [c.strip() for c in select_clause.split(',')]
                for col in columns:
                    # Remove aliases and functions
                    col = re.sub(r'\s+AS\s+\w+', '', col, flags=re.IGNORECASE)
                    col = re.sub(r'^\w+\(', '', col)  # Remove function names
                    col = col.split('.')[-1]  # Get last part after table prefix
                    col = col.strip()
                    
                    if col and col not in ['*', '1', '0']:
                        # Check if column exists in available schema
                        if not any(col.lower() in t.columns for t in schema.tables):
                            logger.debug(f"Potential unknown column: {col}")
        
        return errors
    
    def _validate_safety(self, query: str) -> List[str]:
        """Validate query for safety issues."""
        errors = []
        
        query_upper = query.upper()
        
        # Check for data modification keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                errors.append(f"Dangerous keyword '{keyword}' not allowed")
        
        # Check for SQL injection patterns
        injection_patterns = [
            (r"'?\s*;\s*--", "Comment-based injection attempt"),
            (r"'?\s*;\s*\/\*", "Block comment injection attempt"),
            (r"OR\s+'?1'?\s*=\s*'?1'?", "Always-true condition"),
            (r"UNION\s+SELECT", "UNION injection attempt (use with caution)"),
        ]
        
        for pattern, description in injection_patterns:
            if re.search(pattern, query_upper):
                if "UNION" in pattern:
                    logger.warning(f"Potential issue: {description}")
                else:
                    errors.append(f"Potential security issue: {description}")
        
        # Check for query length (prevent DoS)
        if len(query) > 10000:
            errors.append("Query too long (max 10000 characters)")
        
        return errors
    
    def _extract_tables(self, query: str) -> List[str]:
        """
        Extract table names from SQL query.
        
        Args:
            query: SQL query string
        
        Returns:
            List of table names
        """
        tables = []
        
        # Find FROM clause
        from_pattern = r'FROM\s+(\w+)'
        from_matches = re.findall(from_pattern, query, re.IGNORECASE)
        tables.extend(from_matches)
        
        # Find JOIN clauses
        join_pattern = r'JOIN\s+(\w+)'
        join_matches = re.findall(join_pattern, query, re.IGNORECASE)
        tables.extend(join_matches)
        
        return tables

