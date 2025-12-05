"""
Schema Embeddings for Vector-Based Schema Search.

Generates embeddings for database schema elements to enable semantic search.
Caches embeddings for performance optimization.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from src.rag.sql.schema_manager import SchemaManager
from src.rag.static.embeddings import StaticEmbeddings
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class SchemaEmbeddings:
    """
    Generate and cache embeddings for database schema.
    
    Features:
    - Generate embeddings for tables and columns
    - Vector-based semantic search
    - Embedding caching for performance
    - Query embedding for matching
    """
    
    def __init__(
        self,
        schema_manager: SchemaManager,
        embedding_model: StaticEmbeddings,
        cache_embeddings: bool = True
    ):
        """
        Initialize schema embeddings.
        
        Args:
            schema_manager: SchemaManager instance
            embedding_model: EmbeddingModel for generating vectors
            cache_embeddings: Enable embedding caching
        """
        self.schema_manager = schema_manager
        self.embedding_model = embedding_model
        self.cache_embeddings = cache_embeddings
        
        # Embedding caches
        self._table_embeddings: Dict[str, np.ndarray] = {}
        self._column_embeddings: Dict[str, np.ndarray] = {}
        self._query_embeddings_cache: Dict[str, np.ndarray] = {}
    
    def get_table_embeddings(self, table_names: Optional[List[str]] = None) -> Dict[str, np.ndarray]:
        """
        Get embeddings for tables.
        
        Args:
            table_names: Specific tables to embed (all if None)
        
        Returns:
            Dict mapping table names to embedding vectors
        """
        schema = self.schema_manager.get_schema()
        embeddings = {}
        
        for table in schema.tables:
            if table_names and table.table_name not in table_names:
                continue
            
            if self.cache_embeddings and table.table_name in self._table_embeddings:
                embeddings[table.table_name] = self._table_embeddings[table.table_name]
                continue
            
            description = f"{table.table_name}: {', '.join(table.columns)}"
            embedding = self.embedding_model.embed(description)
            embeddings[table.table_name] = embedding
            
            if self.cache_embeddings:
                self._table_embeddings[table.table_name] = embedding
        
        logger.debug(f"Generated embeddings for {len(embeddings)} tables")
        return embeddings
    
    def get_column_embeddings(self, table_name: str) -> Dict[str, np.ndarray]:
        """
        Get embeddings for columns in a table.
        
        Args:
            table_name: Table to embed columns for
        
        Returns:
            Dict mapping column names to embedding vectors
        """
        table = self.schema_manager.get_table_schema(table_name)
        if not table:
            return {}
        
        embeddings = {}
        cache_key = f"{table_name}:columns"
        
        for column in table.columns:
            col_key = f"{table_name}.{column}"
            if self.cache_embeddings and col_key in self._column_embeddings:
                embeddings[column] = self._column_embeddings[col_key]
                continue
            
            col_type = table.column_types.get(column, "UNKNOWN")
            description = f"{column} ({col_type})"
            embedding = self.embedding_model.embed(description)
            embeddings[column] = embedding
            
            if self.cache_embeddings:
                self._column_embeddings[col_key] = embedding
        
        logger.debug(f"Generated embeddings for {len(embeddings)} columns in {table_name}")
        return embeddings
    
    def find_similar_tables(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Find tables similar to query using embeddings.
        
        Args:
            query: Natural language query
            top_k: Number of top results to return
        
        Returns:
            List of (table_name, similarity_score) tuples, sorted by similarity
        """
        # Get query embedding
        query_embedding = self.embedding_model.embed(query)
        
        table_embeddings = self.get_table_embeddings()
        
        similarities = []
        for table_name, table_embedding in table_embeddings.items():
            similarity = self._cosine_similarity(query_embedding, table_embedding)
            similarities.append((table_name, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = similarities[:top_k]
        
        logger.debug(f"Found {len(results)} similar tables")
        return results
    
    def find_similar_columns(
        self,
        query: str,
        table_name: str,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Find columns similar to query in a specific table.
        
        Args:
            query: Natural language query fragment
            table_name: Table to search columns in
            top_k: Number of top results to return
        
        Returns:
            List of (column_name, similarity_score) tuples
        """
        # Get query embedding
        query_embedding = self.embedding_model.embed(query)
        
        column_embeddings = self.get_column_embeddings(table_name)
        
        similarities = []
        for column_name, column_embedding in column_embeddings.items():
            similarity = self._cosine_similarity(query_embedding, column_embedding)
            similarities.append((column_name, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = similarities[:top_k]
        
        logger.debug(f"Found {len(results)} similar columns in {table_name}")
        return results
    
    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        self._table_embeddings.clear()
        self._column_embeddings.clear()
        self._query_embeddings_cache.clear()
        logger.info("Schema embeddings cache cleared")
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))

