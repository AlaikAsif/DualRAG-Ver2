# RAG Architecture

## Overview
The `rag/` module implements two types of RAG systems:
1. **Static RAG**: Vector-based search over document knowledge base
2. **SQL RAG**: Text-to-SQL for database queries

## Directory Structure

### static/
Vector-based retrieval from document embeddings using FAISS vector database.

### sql/
Database query generation and execution with text-to-SQL and schema embeddings.

## Key Concepts

### Static RAG Flow
```
Document → Chunking → Embeddings (sentence-transformers/all-MiniLM-L6-v2) → FAISS Vector DB → Retrieval
```

### SQL RAG Flow
```
Natural Language → Schema Retrieval → SQL Generation → Query Execution → Result Parsing
```

## Configuration
- Embedding model selection (bge-large recommended)
 - Embedding model selection (default: `sentence-transformers/all-MiniLM-L6-v2`)
- Vector store persistence
- Database connection details
- Query safety constraints

## Recent Changes

- The static vector store now uses FAISS and the code was updated to return the *index directory* (e.g. `data/vectors/static/index`) from `VectorStore.create_vector_store()` instead of a single file path. Callers should provide that directory to loaders or to `Retriever.load_local()`.
- `Retriever.load_local()` accepts either the index file path or the index directory; it will attempt to reconstruct the docstore from `documents.jsonl` if present and will fall back to a raw FAISS search if adapter search methods are incompatible with the installed adapter version.
- Default embedding choice moved to a lightweight sentence-transformers model for faster local testing; switch to larger models as needed in production.
