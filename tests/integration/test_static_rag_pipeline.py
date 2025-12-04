"""Integration tests for the static RAG pipeline.

Tests the full workflow: preprocessing (load/clean/chunk) → indexing → retrieval.
"""
import os
import json
import pytest
import tempfile
import shutil
import numpy as np

from src.preprocessing.loaders import Loader
from src.preprocessing.cleaning import TextCleaner
from src.preprocessing.chunking import Chunker
from src.rag.static.indexer import Indexer
from src.rag.static.retriever import Retriever
from src.rag.static.embeddings import StaticEmbeddings
from src.rag.static.vector_store import VectorStore


class TestStaticRAGPipeline:
    """Integration tests for preprocessing and static RAG retrieval."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.test_index_dir = os.path.join("data", "vectors", "test_index")
        yield
        if os.path.exists(self.test_index_dir):
            shutil.rmtree(self.test_index_dir)

    def test_embeddings_produce_nonzero_vectors(self):
        """Test that StaticEmbeddings produces non-zero embeddings."""
        embedder = StaticEmbeddings()
        texts = ["hello world", "test document", "another example"]
        embeddings = embedder.embed(texts)
        
        assert embeddings.shape == (3, 384)
        assert not np.allclose(embeddings, 0.0)
        assert embeddings.min() >= 0.0
        assert embeddings.max() <= 1.1

    def test_chunking_produces_chunks(self):
        """Test that Chunker produces expected number of chunks."""
        text = "This is a test document. " * 50
        chunks = Chunker.overlapping_chunk_text(text, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_text_cleaning(self):
        """Test text cleaning pipeline."""
        text = "  HELLO   WORLD!!!  "
        cleaned = TextCleaner.normalize(text)
        cleaned = TextCleaner.special_char_removal(cleaned)
        cleaned = TextCleaner.remove_extra_whitespace(cleaned)
        
        assert cleaned == "hello world"

    def test_vector_store_create_and_persist(self):
        """Test VectorStore creation and persistence."""
        vs = VectorStore()
        texts = [
            "Document about apples and oranges",
            "Document about cats and dogs",
            "Document about machine learning"
        ]
        metadatas = [
            {"source": "doc1", "page": 1},
            {"source": "doc2", "page": 1},
            {"source": "doc3", "page": 1}
        ]
        
        idx_dir = vs.create_vector_store(texts, metadatas=metadatas)
        
        assert os.path.exists(idx_dir)
        assert os.path.exists(os.path.join(idx_dir, "documents.jsonl"))
        assert os.path.exists(os.path.join(idx_dir, "embeddings.npy"))
        
        with open(os.path.join(idx_dir, "documents.jsonl"), "r") as f:
            lines = f.readlines()
            assert len(lines) == 3
            for line in lines:
                doc = json.loads(line)
                assert "text" in doc
                assert "metadata" in doc

    def test_indexer_builds_index(self):
        """Test Indexer builds and persists index."""
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Python is a programming language",
            "FAISS provides efficient similarity search"
        ]
        metadatas = [
            {"id": 1},
            {"id": 2},
            {"id": 3}
        ]
        
        idxer = Indexer()
        idx_dir = idxer.build_and_persist_index(texts, metadatas=metadatas)
        
        assert os.path.exists(idx_dir)
        assert os.path.exists(os.path.join(idx_dir, "documents.jsonl"))
        
        emb_path = os.path.join(idx_dir, "embeddings.npy")
        assert os.path.exists(emb_path)
        
        embeddings = np.load(emb_path)
        assert embeddings.shape[0] == 3

    def test_retriever_loads_and_retrieves(self):
        """Test Retriever loads index and performs retrieval."""
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Python is a programming language",
            "FAISS provides efficient similarity search",
            "Database management systems store data"
        ]
        
        idxer = Indexer()
        idx_dir = idxer.build_and_persist_index(texts)
        
        retriever = Retriever.load_local(idx_dir)
        
        query = "what is faiss"
        results = retriever.mmr_rerank(query, initial_k=4, top_k=2)
        
        assert len(results) == 2
        for result in results:
            assert "text" in result
            assert "score" in result
            assert result["score"] is not None
            assert result["score"] >= 0.0

    def test_full_pipeline_with_actual_documents(self):
        """Test full preprocessing and indexing pipeline with actual documents."""
        docs_dir = os.path.join("data", "documents", "raw")
        
        if not os.path.exists(docs_dir) or not os.listdir(docs_dir):
            pytest.skip("No actual documents found for full pipeline test")
        
        pdf_files = [f for f in os.listdir(docs_dir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            pytest.skip("No PDF files in documents/raw directory")
        
        docs = []
        for pdf_file in pdf_files[:1]:
            fp = os.path.join(docs_dir, pdf_file)
            try:
                loaded = Loader.load(fp)
                for doc in loaded:
                    doc.metadata = doc.metadata or {}
                    doc.metadata["source"] = fp
                    docs.append(doc)
            except Exception:
                pass
        
        if not docs:
            pytest.skip("Could not load documents")
        
        cleaned = []
        for doc in docs[:10]:
            text = TextCleaner.normalize(doc.page_content)
            text = TextCleaner.special_char_removal(text)
            text = TextCleaner.remove_extra_whitespace(text)
            text = TextCleaner.filter_english_only(text)
            if text:
                cleaned.append({"text": text, "metadata": doc.metadata})
        
        if not cleaned:
            pytest.skip("No cleaned documents produced")
        
        chunks = []
        metas = []
        for d in cleaned:
            cks = Chunker.overlapping_chunk_text(d["text"], chunk_size=400, chunk_overlap=100)
            for ck in cks:
                chunks.append(ck)
                metas.append(d["metadata"])
        
        assert len(chunks) > 0
        
        idxer = Indexer()
        idx_dir = idxer.build_and_persist_index(chunks, metadatas=metas)
        
        assert os.path.exists(idx_dir)
        
        retriever = Retriever.load_local(idx_dir)
        results = retriever.mmr_rerank("what are the main topics", initial_k=min(10, len(chunks)), top_k=3)
        
        assert len(results) > 0
        assert len(results) <= 3

    def test_retriever_with_metadata_preservation(self):
        """Test that retriever preserves and returns metadata."""
        texts = ["Document A", "Document B", "Document C"]
        metadatas = [
            {"source": "file1.pdf", "page": 1},
            {"source": "file2.pdf", "page": 2},
            {"source": "file3.pdf", "page": 3}
        ]
        
        idxer = Indexer()
        idx_dir = idxer.build_and_persist_index(texts, metadatas=metadatas)
        
        retriever = Retriever.load_local(idx_dir)
        results = retriever.mmr_rerank("Document", initial_k=3, top_k=2)
        
        assert len(results) == 2
        for result in results:
            assert result["metadata"] is not None
            assert "source" in result["metadata"]
            assert "page" in result["metadata"]

    def test_mmr_reranking_returns_diverse_results(self):
        """Test MMR reranking selects diverse results."""
        texts = [
            "Apple is a fruit",
            "Apple is a technology company",
            "Orange is a citrus fruit",
            "Google is a search engine",
            "Neural networks are used in machine learning"
        ]
        
        idxer = Indexer()
        idx_dir = idxer.build_and_persist_index(texts)
        
        retriever = Retriever.load_local(idx_dir)
        results = retriever.mmr_rerank("apple fruit", initial_k=5, top_k=3)
        
        assert len(results) <= 3
        texts_returned = [r["text"] for r in results]
        assert len(set(texts_returned)) == len(texts_returned)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
