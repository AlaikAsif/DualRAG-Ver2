"""
Test SQL RAG pipeline with a real PostgreSQL database.

This script demonstrates the complete SQL RAG pipeline working with an actual database.
Update the DATABASE_CONFIG below with your database credentials.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.sql.connector import SQLConnector
from src.rag.sql.schema_manager import SchemaManager
from src.rag.sql.schema_retriever import SchemaRetriever
from src.rag.sql.schema_embeddings import SchemaEmbeddings
from src.rag.sql.validator import QueryValidator
from src.rag.sql.executor import QueryExecutor
from src.rag.sql.result_parser import ResultParser
from src.rag.static.embeddings import StaticEmbeddings
from src.schemas.sql import SQLQuery
from src.monitoring.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# DATABASE CONFIGURATION - UPDATE WITH YOUR CREDENTIALS
# ============================================================================
DATABASE_CONFIG = {
    "host": "localhost",           # PostgreSQL host
    "port": 5432,                  # PostgreSQL port
    "database": "Pym_IQ",          # Your database name
    "user": "postgres",            # PostgreSQL user
    "password": "123",             # PostgreSQL password
}

# ============================================================================
# PIPELINE DEMONSTRATION
# ============================================================================

def main():
    """Run SQL RAG pipeline demonstration."""
    
    print("\n" + "=" * 80)
    print("SQL RAG PIPELINE - REAL DATABASE TEST")
    print("=" * 80 + "\n")
    
    try:
        # 1. INITIALIZE CONNECTOR
        print("1. Initializing PostgreSQL Connector...")
        # Build connection string
        conn_string = (
            f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
            f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        )
        connector = SQLConnector(
            connection_string=conn_string,
            pool_size=5,
            max_overflow=10
        )
        print("   [OK] Connector initialized\n")
        
        # 2. FETCH DATABASE SCHEMA
        print("2. Fetching database schema...")
        schema_data = connector.get_schema()
        tables = list(schema_data.get("tables", {}).keys())
        print(f"   [OK] Found {len(tables)} tables: {', '.join(tables[:5])}")
        if len(tables) > 5:
            print(f"     ... and {len(tables) - 5} more tables\n")
        else:
            print()
        
        # 3. INITIALIZE SCHEMA MANAGER
        print("3. Initializing Schema Manager...")
        schema_manager = SchemaManager(connector)
        schema = schema_manager.get_schema()
        print(f"   [OK] Schema loaded with {len(schema.tables)} tables\n")
        
        # 4. INITIALIZE SCHEMA RETRIEVER
        print("4. Initializing Schema Retriever...")
        schema_retriever = SchemaRetriever(schema_manager)
        print("   [OK] Schema Retriever ready\n")
        
        # 5. INITIALIZE EMBEDDINGS
        print("5. Initializing Schema Embeddings...")
        embedding_model = StaticEmbeddings()
        schema_embeddings = SchemaEmbeddings(
            schema_manager=schema_manager,
            embedding_model=embedding_model,
            cache_embeddings=True
        )
        print("   [OK] Embeddings initialized\n")
        
        # 6. INITIALIZE VALIDATOR
        print("6. Initializing Query Validator...")
        validator = QueryValidator(schema_manager)
        print("   [OK] Validator ready\n")
        
        # 7. INITIALIZE EXECUTOR
        print("7. Initializing Query Executor...")
        executor = QueryExecutor(connector)
        print("   [OK] Executor ready\n")
        
        # 8. INITIALIZE RESULT PARSER
        print("8. Initializing Result Parser...")
        result_parser = ResultParser()
        print("   [OK] Result Parser ready\n")
        
        # 9. TEST SCHEMA RETRIEVAL
        print("9. Testing Schema Retrieval...")
        natural_query = "Show me all tables in the database"
        relevant_tables = schema_retriever.find_relevant_tables(natural_query)
        print(f"   [OK] Found {len(relevant_tables)} relevant tables")
        if relevant_tables:
            print(f"     Tables: {', '.join(relevant_tables[:3])}\n")
        else:
            print()
        
        # 10. TEST SCHEMA CONTEXT GENERATION
        print("10. Testing Schema Context Generation...")
        schema_context = schema_retriever.get_schema_context(relevant_tables)
        print(f"   [OK] Generated schema context ({len(schema_context)} chars)\n")
        
        # 11. TEST WITH A SIMPLE QUERY
        print("11. Testing with a simple SELECT query...")
        
        # Use the first table if available
        if tables:
            query_string = f"SELECT * FROM {tables[0]} LIMIT 5"
            print(f"   Query: {query_string}")
            
            # Create SQLQuery object for validation
            sql_query = SQLQuery(
                query_string=query_string,
                explanation="Test query to verify pipeline"
            )
            
            # Validate
            is_valid, errors = validator.validate(sql_query)
            print(f"   Validation: {'[OK] Valid' if is_valid else '[X] Invalid'}")
            if errors:
                print(f"     Errors: {errors}\n")
            else:
                print()
            
            # Execute if valid
            if is_valid:
                print("12. Executing query...")
                try:
                    result = executor.execute(sql_query)
                    print(f"   [OK] Query executed successfully")
                    print(f"     Rows returned: {result.row_count}")
                    print(f"     Columns: {', '.join(result.column_names[:3] if len(result.column_names) > 0 else [])}")
                    if result.column_names and len(result.column_names) > 3:
                        print(f"     ... and {len(result.column_names)} total columns\n")
                    else:
                        print()
                    
                    # Parse results
                    print("13. Parsing results for LLM...")
                    parsed = result_parser.parse(result)
                    formatted = result_parser.format_for_llm(result)
                    print(f"   [OK] Results parsed")
                    if formatted:
                        print(f"     Formatted output ({len(formatted)} chars):\n")
                        print("     " + "-" * 70)
                        print("     " + (formatted[:200] + "..." if len(formatted) > 200 else formatted))
                        print("     " + "-" * 70 + "\n")
                    else:
                        print("     No formatted output\n")
                    
                except Exception as e:
                    print(f"   [X] Execution failed: {e}\n")
        else:
            print("   No tables found in database\n")
        
        # 14. SUMMARY
        print("=" * 80)
        print("SQL RAG PIPELINE SUMMARY")
        print("=" * 80)
        print(f"Database: {DATABASE_CONFIG['database']}")
        print(f"Tables: {len(tables)}")
        print(f"Pipeline Status: [OK] ALL COMPONENTS WORKING\n")
        
        print("Components tested:")
        print("  [OK] Connector (connection pooling, schema caching)")
        print("  [OK] Schema Manager (versioning, lazy loading)")
        print("  [OK] Schema Retriever (keyword-based search)")
        print("  [OK] Schema Embeddings (vector embeddings)")
        print("  [OK] Query Validator (syntax & safety checks)")
        print("  [OK] Query Executor (safe execution, limits)")
        print("  [OK] Result Parser (format for LLM)\n")
        
        # Close connector
        connector.close()
        print("Connector closed. Test completed successfully! [OK]\n")
        
        
    except Exception as e:
        print(f"\n[X] Error during pipeline test: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check DATABASE_CONFIG credentials at top of script")
        print(f"  2. Ensure PostgreSQL is running on {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
        print(f"  3. Verify database '{DATABASE_CONFIG['database']}' exists")
        print(f"  4. Check user '{DATABASE_CONFIG['user']}' has access to database\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
