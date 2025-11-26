# Static RAG Setup Guide

## Overview

Static RAG enables searching and synthesizing information from a document knowledge base using vector embeddings.

## Components

1. **Document Loader** - Load PDFs, DOCX, etc.
2. **Text Chunking** - Split documents into semantic chunks
3. **Embedding Model** - Convert text to vectors (BGE-Large)
4. **Vector Store** - Store and search embeddings (Chroma)
5. **Retriever** - Get top-K relevant documents
6. **Synthesizer** - Combine retrieved docs into answer

## Setup Steps

### 1. Install Dependencies
```bash
pip install langchain chroma-db sentence-transformers pypdf python-docx
```

### 2. Download Embedding Model
```bash
python scripts/download_models.py
```

This downloads BGE-Large embedding model locally.

### 3. Initialize Chroma Database
```bash
python scripts/init_static_db.py
```

Creates persistent Chroma database at `data/vectors/static/`.

### 4. Index Documents
```bash
python scripts/seed_data.py
```

Loads sample documents from `data/documents/raw/` and indexes them.

## Configuration

Edit `data/config/static_rag.json`:
```json
{
  "embedding_model": "bge-large",
  "chunk_size": 1024,
  "chunk_overlap": 200,
  "top_k": 5,
  "similarity_threshold": 0.5
}
```

## Data Pipeline

```
documents/raw/*.pdf
    ↓
preprocessing/loaders.py (extract text)
    ↓
preprocessing/chunking.py (semantic chunks)
    ↓
preprocessing/cleaning.py (normalize)
    ↓
rag/static/embeddings.py (create vectors)
    ↓
rag/static/vector_store.py (store in Chroma)
    ↓
data/vectors/static/chroma.sqlite3
```

## Query Flow

```
User: "What does the document say about X?"
    ↓
chains/static_rag_chain.py (query reformulation)
    ↓
rag/static/embeddings.py (embed query)
    ↓
rag/static/retriever.py (semantic search in Chroma)
    ↓
Top-K documents with scores
    ↓
chains/response_synthesizer.py (LLM synthesis)
    ↓
Final answer with citations
```

## Best Practices

- **Chunk Size**: 1024 tokens for balance
- **Overlap**: 200 tokens to maintain context
- **Top-K**: Start with 5, adjust based on quality
- **Similarity Threshold**: 0.5 is good baseline

## Testing

```bash
pytest tests/unit/test_rag/test_embeddings.py
pytest tests/unit/test_rag/test_retriever.py
```

## Performance Tips

1. Pre-index documents during setup
2. Cache popular queries
3. Use GPU for embeddings if available
4. Tune chunk size based on content type
5. Monitor retrieval accuracy metrics

## Troubleshooting

**Low quality results**: 
- Increase top_k
- Decrease similarity_threshold
- Review chunking strategy

**Slow queries**:
- Use GPU for embeddings
- Reduce chunk size
- Index fewer documents

**Out of memory**:
- Reduce batch size
- Use smaller model
- Process documents incrementally
