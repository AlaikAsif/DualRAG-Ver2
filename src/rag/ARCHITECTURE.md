# RAG Architecture

## Overview
The `rag/` module implements two types of RAG systems:
1. **Static RAG**: Vector-based search over document knowledge base
2. **SQL RAG**: Text-to-SQL for database queries

## Directory Structure

### static/
Vector-based retrieval from document embeddings using Chroma vector database.

### sql/
Database query generation and execution with text-to-SQL.

## Key Concepts

### Static RAG Flow
```
Document → Chunking → Embeddings (BGE-Large) → Chroma Vector DB → Retrieval
```

### SQL RAG Flow
```
Natural Language → Schema Retrieval → SQL Generation → Query Execution → Result Parsing
```

## Configuration
- Embedding model selection (bge-large recommended)
- Vector store persistence
- Database connection details
- Query safety constraints
