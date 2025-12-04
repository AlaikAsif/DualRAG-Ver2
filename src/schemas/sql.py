"""
SQL Query and Result Schemas.

Defines Pydantic models for SQL-RAG interactions including query generation,
execution results, and natural language to SQL workflows.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SQLQuery(BaseModel):
    """SQL query to be executed."""
    
    query_string: str = Field(..., min_length=1, description="SQL query text")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters for prepared statements")
    schema_context: Optional[str] = Field(None, description="Relevant database schema info")
    intent: Optional[str] = Field(None, description="Natural language intent for this query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_string": "SELECT * FROM customers WHERE revenue > ?",
                "parameters": {"threshold": 10000},
                "schema_context": "customers(id, name, revenue, region)",
                "intent": "Find top revenue customers"
            }
        }


class SQLResult(BaseModel):
    """Results from executed SQL query."""
    
    query: str = Field(..., description="Original SQL query that was executed")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Query result rows")
    column_names: List[str] = Field(default_factory=list, description="Column names in result set")
    row_count: int = Field(default=0, ge=0, description="Number of rows returned")
    execution_time_ms: float = Field(default=0.0, ge=0.0, description="Query execution time in milliseconds")
    status: str = Field(default="success", description="Query execution status (success, error, timeout)")
    error_message: Optional[str] = Field(None, description="Error message if query failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "SELECT name, revenue FROM customers LIMIT 5",
                "rows": [
                    {"name": "Acme Corp", "revenue": 50000},
                    {"name": "TechStart Inc", "revenue": 75000}
                ],
                "column_names": ["name", "revenue"],
                "row_count": 2,
                "execution_time_ms": 125.5,
                "status": "success"
            }
        }


class SQLRagRequest(BaseModel):
    """Natural language request for SQL RAG (convert NL to SQL)."""
    
    query: str = Field(..., min_length=1, description="Natural language query")
    database_context: str = Field(..., description="Available tables and schema info")
    schema_summary: Optional[str] = Field(None, description="High-level database schema summary")
    previous_queries: List[str] = Field(default_factory=list, description="Previous successful queries for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me the top 5 customers by revenue",
                "database_context": "Available tables: customers, orders, products",
                "schema_summary": "customers(id, name, revenue), orders(id, customer_id, amount)",
                "previous_queries": []
            }
        }


class SQLRagResponse(BaseModel):
    """Complete SQL RAG response with generated query and results."""
    
    original_query: str = Field(..., description="Original natural language query")
    generated_sql: str = Field(..., description="SQL query generated from NL")
    sql_explanation: Optional[str] = Field(None, description="Explanation of the SQL query")
    query_result: SQLResult = Field(..., description="Results from executing the SQL")
    interpretation: str = Field(..., description="Natural language interpretation of results")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in SQL generation (0-1)")
    generated_at: datetime = Field(default_factory=datetime.now, description="When response was generated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "Top customers by revenue",
                "generated_sql": "SELECT name, revenue FROM customers ORDER BY revenue DESC LIMIT 5",
                "sql_explanation": "This query retrieves the 5 customers with highest revenue.",
                "query_result": {
                    "query": "SELECT name, revenue FROM customers ORDER BY revenue DESC LIMIT 5",
                    "rows": [{"name": "Acme", "revenue": 100000}],
                    "column_names": ["name", "revenue"],
                    "row_count": 5,
                    "execution_time_ms": 145.0,
                    "status": "success"
                },
                "interpretation": "The top customer is Acme Corp with $100,000 in revenue.",
                "confidence": 0.95
            }
        }


class SchemaTable(BaseModel):
    """Database table schema information."""
    
    table_name: str = Field(..., description="Name of the table")
    columns: List[str] = Field(..., description="List of column names")
    column_types: Dict[str, str] = Field(default_factory=dict, description="Column name to data type mapping")
    primary_key: Optional[str] = Field(None, description="Primary key column")
    sample_rows: int = Field(default=0, ge=0, description="Number of sample rows shown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "customers",
                "columns": ["id", "name", "email", "revenue"],
                "column_types": {"id": "INT", "name": "VARCHAR", "revenue": "DECIMAL"},
                "primary_key": "id",
                "sample_rows": 1000
            }
        }


class DatabaseSchema(BaseModel):
    """Complete database schema information."""
    
    database_name: str = Field(..., description="Database name")
    tables: List[SchemaTable] = Field(..., description="All tables in database")
    relationships: Dict[str, List[str]] = Field(default_factory=dict, description="Foreign key relationships")
    last_updated: datetime = Field(default_factory=datetime.now, description="When schema was last updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "database_name": "sales_db",
                "tables": [
                    {
                        "table_name": "customers",
                        "columns": ["id", "name", "revenue"],
                        "column_types": {"id": "INT", "name": "VARCHAR", "revenue": "DECIMAL"},
                        "primary_key": "id"
                    }
                ],
                "relationships": {
                    "orders.customer_id": ["customers.id"]
                }
            }
        }
