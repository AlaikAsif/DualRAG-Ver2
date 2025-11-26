# Schemas Architecture

## Overview
The `schemas/` module contains Pydantic models for type validation and data structures.

## Components

### decisions.py
- LLM routing decision types
- Decision validation
- Routing options enum

### chat.py
- ChatRequest/ChatResponse models
- Message types
- Conversation metadata

### rag.py
- RAG query/result models
- Retrieved document types
- Relevance scores

### sql.py
- SQL query/result models
- Database response types
- Error types

### report.py
- Report customization models
- Report output types
- Template options

### followup.py
- Follow-up response models
- Context preservation types

## Benefits
- Type safety across system
- API validation
- Documentation through types
- IDE autocomplete support
