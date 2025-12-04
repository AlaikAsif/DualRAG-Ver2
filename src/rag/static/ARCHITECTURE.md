# Static RAG Architecture

## Overview
Static RAG handles retrieval from a knowledge base of documents using vector embeddings.

## Components

### embeddings.py
- Default: `sentence-transformers/all-MiniLM-L6-v2` (lightweight)
- Convert text to embeddings
- Manage embedding cache

### vector_store.py
- faiss vector database management
- Persistent storage configuration
- Collection management (supports adapter-backed append when available, otherwise rebuild-based incremental updates)
- Uses a simple filesystem lock during index persistence to avoid concurrent-writer corruption

### retriever.py
- Document retrieval logic
- Similarity search
- Result ranking and filtering

### indexer.py
- Document indexing pipeline
- Batch processing
- Update management

## Data Flow
```
PDF/Document → Preprocessing → Chunking → Embeddings → faiss DB
                                                          ↓
User Query → Embedding → Semantic Search → Top-K Results → LLM Synthesis
```

## Performance Considerations
- Chunk size and overlap
- Embedding model optimization
- Vector search parameters (top-k)
- Caching strategies

## Recent Changes

- `VectorStore.create_vector_store()` now returns the index directory (e.g. `data/vectors/static/index`) instead of a single index file. This makes it consistent with adapter-backed persistence that may write multiple files in the index folder.
- `Retriever.load_local()` was hardened to accept either directory or file paths, reconstruct the in-memory docstore from `documents.jsonl` when available, and fall back to a raw FAISS search if the installed FAISS adapter behaves differently across versions.
