"""
Integration tests for complete SQL RAG pipeline.

Tests the flow: Schema Retrieval -> LLM Generation -> Validation -> Execution -> Result Parsing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.rag.sql.connector import SQLConnector
from src.rag.sql.schema_manager import SchemaManager
from src.rag.sql.schema_retriever import SchemaRetriever
from src.rag.sql.schema_embeddings import SchemaEmbeddings
from src.rag.sql.query_generator import QueryGenerator
from src.rag.sql.executor import QueryExecutor
from src.rag.sql.validator import QueryValidator
from src.rag.sql.result_parser import ResultParser
from src.schemas.sql import (
    SQLQuery, SQLResult, SQLRagRequest,
    SchemaTable, DatabaseSchema
)


@pytest.fixture
def mock_connector():
    """Create mock SQLConnector."""
    connector = Mock(spec=SQLConnector)
    connector.database = "test_db"
    
    # Mock schema response
    connector.get_schema.return_value = {
        'tables': {
            'users': {
                'columns': [
                    {'name': 'id', 'type': 'INT'},
                    {'name': 'name', 'type': 'VARCHAR'},
                    {'name': 'email', 'type': 'VARCHAR'}
                ]
            },
            'orders': {
                'columns': [
                    {'name': 'id', 'type': 'INT'},
                    {'name': 'user_id', 'type': 'INT'},
                    {'name': 'amount', 'type': 'DECIMAL'}
                ]
            }
        }
    }
    
    return connector


@pytest.fixture
def schema_manager(mock_connector):
    """Create SchemaManager."""
    return SchemaManager(mock_connector)


@pytest.fixture
def schema_retriever(schema_manager):
    """Create SchemaRetriever."""
    return SchemaRetriever(schema_manager)


@pytest.fixture
def mock_embedding_model():
    """Create mock embedding model."""
    model = Mock()
    model.embed.return_value = __import__('numpy').array([0.1, 0.2, 0.3])
    return model


@pytest.fixture
def schema_embeddings(schema_manager, mock_embedding_model):
    """Create SchemaEmbeddings."""
    return SchemaEmbeddings(schema_manager, mock_embedding_model)


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    llm = Mock()
    llm.generate.return_value = "SELECT * FROM users WHERE id = 1"
    return llm


@pytest.fixture
def query_generator(schema_retriever, schema_embeddings, mock_llm_client):
    """Create QueryGenerator."""
    return QueryGenerator(
        mock_llm_client,
        schema_retriever,
        schema_embeddings
    )


@pytest.fixture
def query_validator(schema_manager):
    """Create QueryValidator."""
    return QueryValidator(schema_manager)


@pytest.fixture
def query_executor(mock_connector):
    """Create QueryExecutor."""
    return QueryExecutor(mock_connector)


@pytest.fixture
def result_parser():
    """Create ResultParser."""
    return ResultParser()


class TestSQLRAGPipeline:
    """Test complete SQL RAG pipeline integration."""
    
    def test_schema_retrieval_integration(self, schema_retriever):
        """Test SchemaRetriever finds relevant tables."""
        relevant = schema_retriever.find_relevant_tables("find users by email")
        
        assert len(relevant) > 0
        assert any(t.table_name == "users" for t in relevant)
    
    def test_schema_retriever_context_generation(self, schema_retriever):
        """Test SchemaRetriever generates schema context."""
        context = schema_retriever.get_schema_context()
        
        assert "users" in context
        assert "orders" in context
        assert "email" in context
    
    def test_schema_embeddings_caching(self, schema_embeddings, mock_embedding_model):
        """Test SchemaEmbeddings caches embeddings."""
        # First call
        embeddings1 = schema_embeddings.get_table_embeddings()
        call_count_1 = mock_embedding_model.embed.call_count
        
        # Second call (should use cache)
        embeddings2 = schema_embeddings.get_table_embeddings()
        call_count_2 = mock_embedding_model.embed.call_count
        
        # Should not call embed again (using cache)
        assert call_count_2 == call_count_1
        assert len(embeddings1) > 0
    
    def test_query_generator_produces_valid_sql(self, query_generator):
        """Test QueryGenerator produces valid SQL."""
        request = SQLRagRequest(
            query="Show all users",
            database_context="users table with id, name, email"
        )
        
        sql_query, explanation, confidence = query_generator.generate(request)
        
        assert isinstance(sql_query, SQLQuery)
        assert sql_query.query_string
        assert "SELECT" in sql_query.query_string.upper()
        assert 0 <= confidence <= 1
    
    def test_validator_accepts_valid_query(self, query_validator):
        """Test QueryValidator accepts valid queries."""
        query = SQLQuery(query_string="SELECT * FROM users")
        
        is_valid, errors = query_validator.validate(query)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validator_rejects_dangerous_queries(self, query_validator):
        """Test QueryValidator rejects dangerous queries."""
        query = SQLQuery(query_string="DROP TABLE users")
        
        is_valid, errors = query_validator.validate(query)
        
        assert not is_valid
        assert len(errors) > 0
        assert any("DROP" in str(e) for e in errors)
    
    def test_executor_success_flow(self, query_executor, mock_connector):
        """Test QueryExecutor successful execution."""
        mock_connector.execute_query.return_value = {
            'rows': [{'id': 1, 'name': 'John'}],
            'column_names': ['id', 'name'],
            'row_count': 1,
            'status': 'success',
            'error_message': None
        }
        
        query = SQLQuery(query_string="SELECT * FROM users")
        result = query_executor.execute(query)
        
        assert result.status == 'success'
        assert result.row_count == 1
        assert len(result.rows) == 1
    
    def test_result_parser_formats_success(self, result_parser):
        """Test ResultParser formats successful results."""
        result = SQLResult(
            query="SELECT * FROM users",
            rows=[{'id': 1, 'name': 'John'}],
            column_names=['id', 'name'],
            row_count=1,
            execution_time_ms=50.0,
            status='success'
        )
        
        parsed = result_parser.parse(result)
        
        assert parsed['status'] == 'success'
        assert parsed['row_count'] == 1
        assert 'summary' in parsed
        assert 'formatted_text' in parsed
    
    def test_result_parser_formats_error(self, result_parser):
        """Test ResultParser formats error results."""
        result = SQLResult(
            query="SELECT * FROM unknown",
            rows=[],
            column_names=[],
            row_count=0,
            execution_time_ms=10.0,
            status='error',
            error_message='Table "unknown" does not exist'
        )
        
        parsed = result_parser.parse(result)
        
        assert parsed['status'] == 'error'
        assert 'error_message' in parsed
        assert 'error_type' in parsed
        assert parsed['error_type'] == 'schema_error'
    
    def test_complete_pipeline_flow(
        self,
        schema_retriever,
        query_generator,
        query_validator,
        query_executor,
        result_parser,
        mock_connector
    ):
        """Test complete pipeline flow from query to result."""
        # Setup mock executor response
        mock_connector.execute_query.return_value = {
            'rows': [{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}],
            'column_names': ['id', 'name'],
            'row_count': 2,
            'status': 'success',
            'error_message': None
        }
        
        # Step 1: Get schema context
        context = schema_retriever.get_schema_context()
        assert len(context) > 0
        
        # Step 2: Generate query
        request = SQLRagRequest(
            query="List all users",
            database_context=context
        )
        sql_query, explanation, confidence = query_generator.generate(request)
        assert isinstance(sql_query, SQLQuery)
        
        # Step 3: Validate query
        is_valid, errors = query_validator.validate(sql_query)
        assert is_valid, f"Validation failed: {errors}"
        
        # Step 4: Execute query
        result = query_executor.execute(sql_query)
        assert result.status == 'success'
        
        # Step 5: Parse results
        parsed = result_parser.parse(result)
        assert parsed['status'] == 'success'
        assert parsed['row_count'] == 2
        assert 'formatted_text' in parsed


class TestSQLRAGDataFlow:
    """Test data flow between components."""
    
    def test_schema_manager_to_retriever(self, schema_manager, schema_retriever):
        """Test SchemaManager output is usable by SchemaRetriever."""
        schema = schema_manager.get_schema()
        
        # SchemaRetriever should work with SchemaManager
        assert isinstance(schema, DatabaseSchema)
        assert len(schema.tables) > 0
        
        # Should be able to get table info
        table = schema_retriever.get_table_info('users')
        assert table is not None
        assert table.table_name == 'users'
    
    def test_retriever_output_to_generator(self, schema_retriever, query_generator):
        """Test SchemaRetriever output works with QueryGenerator."""
        context = schema_retriever.get_schema_context()
        
        # QueryGenerator should accept this context
        request = SQLRagRequest(
            query="find users",
            database_context=context
        )
        
        sql_query, _, _ = query_generator.generate(request)
        assert sql_query is not None
    
    def test_generator_output_to_validator(self, query_generator, query_validator):
        """Test QueryGenerator output is validated correctly."""
        request = SQLRagRequest(
            query="get all orders",
            database_context="orders table"
        )
        
        sql_query, _, _ = query_generator.generate(request)
        
        # Should be valid SQLQuery
        assert isinstance(sql_query, SQLQuery)
        is_valid, errors = query_validator.validate(sql_query)
        # Might have errors depending on schema, but should be checkable
        assert isinstance(errors, list)
    
    def test_validator_output_to_executor(self, query_validator, query_executor):
        """Test validated query works with executor."""
        query = SQLQuery(query_string="SELECT id FROM users LIMIT 10")
        
        is_valid, errors = query_validator.validate(query)
        assert is_valid
        
        # Should be executable
        result = query_executor.execute(query)
        assert isinstance(result, SQLResult)
    
    def test_executor_output_to_parser(self, query_executor, result_parser, mock_connector):
        """Test executor output is parseable."""
        mock_connector.execute_query.return_value = {
            'rows': [{'id': 1}],
            'column_names': ['id'],
            'row_count': 1,
            'status': 'success',
            'error_message': None
        }
        
        query = SQLQuery(query_string="SELECT id FROM users LIMIT 1")
        result = query_executor.execute(query)
        
        # Should be parseable
        parsed = result_parser.parse(result)
        assert 'status' in parsed
        assert 'summary' in parsed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
