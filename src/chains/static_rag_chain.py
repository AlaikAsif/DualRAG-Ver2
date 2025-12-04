"""
Static RAG Chain: Document retrieval and context-augmented response generation.

This chain loads a persisted FAISS index, retrieves relevant documents based on user queries,
and generates responses augmented with retrieved context. Integrates with LLM, prompts, and monitoring.
"""

from typing import Optional, Dict, Any, List
import time

from src.rag.static.retriever import Retriever
from src.chains.llm import LLM
from src.prompts.static_rag_prompts import (
    STATIC_RAG_SYSTEM_PROMPT,
    STATIC_RAG_QUERY_PROMPT_STRICT,
)
from src.schemas.rag import RAGResponse, SourceDocument
from src.monitoring.logger import get_logger
from src.monitoring.tracer import trace_chain_execution
from src.utils.config import get_config
from src.utils.retry import retry_with_backoff

logger = get_logger(__name__)
config = get_config()


class StaticRAGChain:
    """
    Static RAG Chain for document retrieval and response generation.
    
    Workflow:
    1. Load persisted FAISS index from disk.
    2. Retrieve relevant documents using MMR reranking.
    3. Augment user query with retrieved context.
    4. Generate response using LLM.
    5. Track metrics and log execution details.
    
    Attributes:
        retriever (StaticRetriever): Loads and queries FAISS index.
        llm: Language model for response generation.
        index_path (str): Path to persisted FAISS index directory.
        retrieval_k (int): Number of documents to retrieve per query.
        initial_k (int): Candidates to fetch before MMR reranking.
        use_mmr (bool): Enable MMR reranking for diverse results.
    """
    
    def __init__(
        self,
        index_path: str = "data/vectors/static/index",
        retrieval_k: int = 3,
        initial_k: int = 10,
        use_mmr: bool = True,
        llm: Optional[LLM] = None,
    ):
        """
        Initialize StaticRAGChain.
        
        Args:
            index_path: Path to persisted FAISS index directory.
            retrieval_k: Number of documents to retrieve per query.
            initial_k: Candidates to fetch before MMR reranking (if use_mmr=True).
            use_mmr: Enable MMR reranking for diversity.
            llm: Language model instance. If None, creates default LLM.
        
        Raises:
            FileNotFoundError: If index_path does not exist.
        """
        self.index_path = index_path
        self.retrieval_k = retrieval_k
        self.initial_k = initial_k
        self.use_mmr = use_mmr
        self.llm = llm or self._create_default_llm()
        
        # Load retriever with index
        try:
            self.retriever = Retriever.load_local(index_path)
            logger.info(f"✓ Loaded FAISS index from {index_path}")
        except FileNotFoundError as e:
            logger.error(f"Index not found at {index_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load index: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _create_default_llm() -> LLM:
        """Create default LLM from config."""
        llm_url = config.get("llm.url", "http://localhost:11434")
        llm_model = config.get("llm.model", "granite3-dense:8b")
        return LLM(url=llm_url, model=llm_model)
    
    @trace_chain_execution(chain_name="static_rag")
    def retrieve_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for the query using MMR or similarity search.
        
        Args:
            query: User query string.
        
        Returns:
            List of documents with metadata:
            [
                {
                    "content": "document text",
                    "score": 0.75,
                    "metadata": {"source": "file.pdf", "page": 1}
                },
                ...
            ]
        """
        try:
            if self.use_mmr:
                results = self.retriever.mmr_rerank(
                    query=query,
                    initial_k=self.initial_k,
                    top_k=self.retrieval_k,
                )
            else:
                results = self.retriever.similarity_search_documents(
                    query=query,
                    k=self.retrieval_k,
                )
            
            logger.info(f"Retrieved {len(results)} documents for query: {query[:60]}...")
            return results
        
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query}': {e}", exc_info=True)
            return []
    
    def _format_retrieved_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into a readable context string.
        
        Args:
            documents: List of retrieved document dicts.
        
        Returns:
            Formatted context string with document content and metadata.
        """
        if not documents:
            return "(No relevant documents found)"
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")
            score = doc.get("score", 0.0)
            metadata = doc.get("metadata", {})
            
            source_info = ""
            if metadata:
                if isinstance(metadata, dict):
                    source = metadata.get("source", "unknown")
                    page = metadata.get("page", "")
                    source_info = f" (Source: {source}" + (f", Page: {page}" if page else "") + ")"
                else:
                    source_info = f" (Metadata: {metadata})"
            
            context_parts.append(
                f"[Document {i}, Score: {score:.2f}]{source_info}\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _generate_response_with_context(
        self,
        query: str,
        context: str,
    ) -> str:
        """
        Generate LLM response augmented with retrieved context.
        
        Args:
            query: Original user query.
            context: Formatted retrieved documents.
        
        Returns:
            Generated response string.
        
        Raises:
            Exception: If LLM generation fails after retries.
        """
        # Format prompt with context
        prompt = STATIC_RAG_QUERY_PROMPT_STRICT.format(
            context=context,
            query=query,
        )
        
        try:
            response = self.llm.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}", exc_info=True)
            raise
    
    @trace_chain_execution(chain_name="static_rag")
    def invoke(
        self,
        query: str,
        include_sources: bool = True,
        return_schema: bool = True,
    ) -> Optional[Any]:
        """
        Execute the full static RAG chain: retrieve documents → augment context → generate response.
        
        Args:
            query: User query string.
            include_sources: Whether to include source metadata in response.
            return_schema: If True, returns RAGResponse schema. If False, returns raw response string.
        
        Returns:
            RAGResponse with generated response and retrieved documents, or string if return_schema=False.
            Returns None if chain execution fails.
        """
        try:
            start_time = time.time()
            
            # Step 1: Retrieve documents
            documents = self.retrieve_documents(query)
            
            # Step 2: Format context
            context = self._format_retrieved_context(documents)
            
            # Step 3: Generate response
            response_text = self._generate_response_with_context(query, context)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"✓ Static RAG chain completed in {elapsed_ms:.2f}ms")
            
            # Step 4: Return schema or raw response
            if return_schema:
                return RAGResponse(
                    response=response_text,
                    source_documents=[
                        SourceDocument(
                            content=doc.get("content", ""),
                            metadata=doc.get("metadata", {}),
                            score=doc.get("score", 0.0),
                        )
                        for doc in documents
                    ] if include_sources else [],
                    retrieval_count=len(documents),
                    chain_name="static_rag",
                )
            else:
                return response_text
        
        except Exception as e:
            logger.error(f"Static RAG chain failed: {e}", exc_info=True)
            return None
    
    def batch_retrieve(
        self,
        queries: List[str],
    ) -> List[List[Dict[str, Any]]]:
        """
        Retrieve documents for multiple queries in batch.
        
        Args:
            queries: List of query strings.
        
        Returns:
            List of document lists, one per query.
        """
        results = []
        for query in queries:
            docs = self.retrieve_documents(query)
            results.append(docs)
        return results


def create_static_rag_chain(
    index_path: Optional[str] = None,
    retrieval_k: int = 3,
    use_mmr: bool = True,
) -> StaticRAGChain:
    """
    Factory function to create a StaticRAGChain instance with config defaults.
    
    Args:
        index_path: Override default index path. Uses config value if None.
        retrieval_k: Number of documents to retrieve.
        use_mmr: Enable MMR reranking.
    
    Returns:
        Initialized StaticRAGChain instance.
    """
    index_path = index_path or config.get(
        "rag.static.index_path",
        "data/vectors/static/index",
    )
    return StaticRAGChain(
        index_path=index_path,
        retrieval_k=retrieval_k,
        use_mmr=use_mmr,
    )


if __name__ == "__main__":
    # Example usage
    chain = create_static_rag_chain(retrieval_k=3, use_mmr=True)
    
    query = "What are the main features of this product?"
    result = chain.invoke(query, include_sources=True, return_schema=True)
    
    if result:
        print(f"Query: {query}")
        print(f"Response: {result.response}")
        print(f"Documents Retrieved: {result.retrieval_count}")
        for i, doc in enumerate(result.source_documents, 1):
            print(f"  [{i}] {doc.content[:100]}... (Score: {doc.score:.2f})")
    else:
        print("Chain execution failed.")
