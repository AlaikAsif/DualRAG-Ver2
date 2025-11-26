# SQL RAG Architecture

## Overview
SQL RAG handles natural language to SQL conversion and safe database query execution.

## Components

### connector.py
- Database connection (PostgreSQL/MySQL)
- Connection pooling
- Schema caching

### schema_retriever.py
- Retrieve relevant database schema
- Column and table information
- Relationship mapping

### query_generator.py
- LLM-based SQL generation
- Schema-aware query construction
- Query validation

### executor.py
- Safe query execution
- Permission checks
- Result limiting

### result_parser.py
- Parse SQL results
- Format for LLM consumption
- Error handling

## Data Flow
```
Natural Language Query
         ↓
Schema Retrieval (relevant tables/columns)
         ↓
LLM SQL Generation (with schema context)
         ↓
Query Validation (safety checks)
         ↓
Execution (with limits)
         ↓
Result Parsing → LLM Synthesis
```

## Safety Considerations
- Read-only query enforcement
- Result limiting (max rows)
- Timeout protection
- Audit logging
