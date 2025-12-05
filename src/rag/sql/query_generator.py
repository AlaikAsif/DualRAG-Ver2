"""
LLM-Based SQL Query Generation.

Generates SQL queries from natural language using LLM with schema context.
Supports schema-aware query construction and iterative refinement.
"""

from typing import Optional
from src.rag.sql.schema_retriever import SchemaRetriever
from src.rag.sql.schema_embeddings import SchemaEmbeddings
from src.chains.llm import LLM
from src.schemas.sql import SQLQuery, SQLRagRequest
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class QueryGenerator:
    """
    Generate SQL queries from natural language using LLM.
    
    Features:
    - Schema-aware query generation
    - Multi-turn conversation support
    - Query confidence scoring
    - Query explanation generation
    """
    
    def __init__(
        self,
        llm_client: LLM,
        schema_retriever: SchemaRetriever,
        schema_embeddings: Optional[SchemaEmbeddings] = None,
        max_retries: int = 2
    ):
        """
        Initialize query generator.
        
        Args:
            llm_client: LLM client for query generation
            schema_retriever: SchemaRetriever for schema context
            schema_embeddings: Optional SchemaEmbeddings for semantic search
            max_retries: Max retries on invalid queries
        """
        self.llm_client = llm_client
        self.schema_retriever = schema_retriever
        self.schema_embeddings = schema_embeddings
        self.max_retries = max_retries
    
    def generate(
        self,
        request: SQLRagRequest,
        include_explanation: bool = True
    ) -> tuple[SQLQuery, str, float]:

        logger.info(f"Generating SQL for: {request.query[:100]}")
        
        # Find relevant tables
        relevant_tables = self.schema_retriever.find_relevant_tables(
            request.query,
            max_tables=5
        )
        relevant_table_names = [t.table_name for t in relevant_tables]
        
        # Generate schema context
        schema_context = self.schema_retriever.get_schema_context(
            relevant_table_names if relevant_tables else None
        )
        
        # Build prompt with context
        prompt = self._build_prompt(
            request.query,
            schema_context,
            request.schema_summary,
            request.previous_queries
        )
        
        logger.debug(f"Generated prompt (length: {len(prompt)})")
        
        # Generate SQL with LLM
        sql_query = self.llm_client.generate(prompt)
        
        # Parse response
        parsed_sql = self._parse_response(sql_query)
        
        # Extract explanation if requested
        explanation = ""
        if include_explanation:
            explanation = self._generate_explanation(parsed_sql)
        
        # Estimate confidence
        confidence = self._estimate_confidence(parsed_sql, relevant_table_names)
        
        logger.info(f"Generated SQL: {parsed_sql[:100]}... (confidence: {confidence:.2f})")
        
        # Create SQLQuery object
        sql_obj = SQLQuery(
            query_string=parsed_sql,
            parameters={},
            schema_context=schema_context,
            intent=request.query
        )
        
        return sql_obj, explanation, confidence
    
    def _build_prompt(
        self,
        query: str,
        schema_context: str,
        schema_summary: Optional[str],
        previous_queries: list[str]
    ) -> str:
        """Build LLM prompt with context."""
        prompt_lines = [
            "You are a SQL expert. Generate a PostgreSQL query for the following request.",
            "",
            "Database Schema:",
            schema_context,
        ]
        
        if schema_summary:
            prompt_lines.extend([
                "",
                "Schema Summary:",
                schema_summary
            ])
        
        if previous_queries:
            prompt_lines.extend([
                "",
                "Previous successful queries for reference:",
                *[f"- {q}" for q in previous_queries[:3]]
            ])
        
        prompt_lines.extend([
            "",
            "User Request:",
            query,
            "",
            "Generate ONLY the SQL query, no explanation. Start with SELECT."
        ])
        
        return "\n".join(prompt_lines)
    
    def _parse_response(self, response: str) -> str:
        """
        Parse LLM response to extract SQL query.
        
        Args:
            response: LLM response text
        
        Returns:
            Cleaned SQL query
        """
        # Remove markdown code blocks if present
        response = response.strip()
        
        if response.startswith("```sql"):
            response = response[6:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        # Extract first SQL statement
        response = response.strip()
        
        # Remove trailing semicolon
        if response.endswith(";"):
            response = response[:-1]
        
        return response.strip()
    
    def _generate_explanation(self, sql: str) -> str:
        prompt = f"""Provide a brief one-line explanation of this SQL query:{sql} Explanation:"""
        
        explanation = self.llm_client.generate(prompt)
        return explanation.strip()
    
    def _estimate_confidence(self, sql: str, relevant_tables: list[str]) -> float:
        """
        Estimate confidence in generated query.
        
        Args:
            sql: Generated SQL query
            relevant_tables: Tables found in schema
        
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence
        
        sql_upper = sql.upper()
        
        # Check for SELECT statement
        if sql_upper.startswith("SELECT"):
            confidence += 0.2
        
        # Check for relevant table usage
        table_count = sum(1 for table in relevant_tables if table.upper() in sql_upper)
        if table_count > 0:
            confidence += 0.15 * min(table_count / len(relevant_tables), 1.0)
        
        # Check for FROM clause
        if "FROM" in sql_upper:
            confidence += 0.1
        
        # Penalize for suspicious patterns
        if "--" in sql or "/*" in sql:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))

