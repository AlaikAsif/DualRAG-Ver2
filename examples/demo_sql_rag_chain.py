"""
SQL RAG Chain demonstration script.

Shows how to use the complete SQL RAG pipeline to convert natural language
to SQL queries, execute them, and return formatted results.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chains.sql_rag_chain import SQLRAGChain
from src.schemas.sql import SQLRagRequest
from src.monitoring.logger import get_logger

logger = get_logger(__name__)

# Database configuration
DATABASE_URL = "postgresql://postgres:123@localhost:5432/Pym_IQ"


def main():
    """Demonstrate SQL RAG Chain."""
    
    print("\n" + "=" * 80)
    print("SQL RAG CHAIN DEMONSTRATION")
    print("=" * 80 + "\n")
    
    try:
        # Initialize chain
        print("[1/4] Initializing SQL RAG Chain...")
        chain = SQLRAGChain(
            connection_string=DATABASE_URL,
            max_retries=2,
            confidence_threshold=0.5,
            enable_embeddings=True
        )
        print("      [OK] Chain initialized\n")
        
        # Show schema summary
        print("[2/4] Database Schema Summary:")
        print("      " + "-" * 70)
        schema = chain.get_schema_summary()
        for line in schema.split("\n")[:10]:
            print(f"      {line}")
        print("      " + "-" * 70 + "\n")
        
        # Example queries
        example_queries = [
            "What tables are in the database?",
            "Show me the migration history",
            "How many tables do we have?",
        ]
        
        # Process queries
        print("[3/4] Processing Natural Language Queries:\n")
        
        for i, natural_query in enumerate(example_queries, 1):
            print(f"Query {i}: {natural_query}")
            
            try:
                # Create request
                request = SQLRagRequest(
                    query=natural_query,
                    database_context="Database with multiple tables"
                )
                
                # Process through chain
                response = chain.process(request)
                
                print(f"SQL Generated: {response.generated_sql[:80]}...")
                print(f"Confidence: {response.confidence:.2f}")
                print(f"Explanation: {response.sql_explanation[:80] if response.sql_explanation else 'N/A'}...")
                print(f"Result Rows: {response.query_result.row_count}")
                print(f"Interpretation: {response.interpretation[:100]}...")
                print()
                
            except Exception as e:
                print(f"Error processing query: {e}\n")
        
        # Get execution history
        print("[4/4] Recent Query Execution History:")
        history = chain.get_execution_history(limit=5)
        if history:
            print(f"      Total executed queries: {len(history)}")
            for entry in history[:3]:
                print(f"      - {entry}\n")
        else:
            print("      No query history available\n")
        
        # Close chain
        chain.close()
        
        print("=" * 80)
        print("SQL RAG CHAIN DEMONSTRATION COMPLETE")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)
        print(f"\nError: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
