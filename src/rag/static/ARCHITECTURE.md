# Static RAG Architecture

## Overview
Static RAG handles retrieval from a knowledge base of documents using vector embeddings.

## Components

### embeddings.py
- Initialize BGE-Large embedding model
- Convert text to embeddings
- Manage embedding cache

### vector_store.py
- Chroma vector database management
- Persistent storage configuration
- Collection management

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
PDF/Document → Preprocessing → Chunking → Embeddings → Chroma DB
                                                          ↓
User Query → Embedding → Semantic Search → Top-K Results → LLM Synthesis
```

## Performance Considerations
- Chunk size and overlap
- Embedding model optimization
- Vector search parameters (top-k)
- Caching strategies
