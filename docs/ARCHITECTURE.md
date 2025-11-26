# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (UI)                          │
│              HTML/JS Chat Interface                          │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                       API Layer                              │
│                  FastAPI Routes & Middleware                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  LLM Orchestrator (🔥 MAIN)                 │
│            Makes ALL routing decisions                       │
│         ┌─ Chat Response                                    │
│         ├─ Static RAG Query                                 │
│         ├─ SQL Query                                        │
│         ├─ Report Generation                                │
│         └─ Follow-up Handling                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
   ┌─────────┐        ┌─────────┐        ┌──────────┐
   │ Static  │        │   SQL   │        │ General  │
   │  RAG    │        │  RAG    │        │  Chat    │
   └─────────┘        └─────────┘        └──────────┘
        ↓                   ↓                   ↓
   ┌─────────┐        ┌──────────┐        ┌──────────┐
   │ Chroma  │        │Database  │        │ Ollama   │
   │  VStore │        │(Postgres)│        │  LLM     │
   └─────────┘        └──────────┘        └──────────┘
        ↓                   ↓                   ↓
        └───────────────────┼───────────────────┘
                            ↓
                 ┌─────────────────────┐
                 │Response Synthesizer │
                 │ Combines all results│
                 └─────────────────────┘
                            ↓
                      Final Response
```

## Key Principles

1. **LLM-Driven Orchestration**: The orchestrator LLM makes ALL routing decisions, not hard-coded rules
2. **Modular Design**: Each component (chains, RAG, etc.) is independent and testable
3. **Type Safety**: Pydantic schemas for all data structures
4. **Observability**: Comprehensive logging and metrics
5. **Error Handling**: Graceful fallbacks and retry logic

## Component Directory

### src/chains/ 🔥
Core LLM interaction logic and orchestration

### src/rag/
Retrieval systems (static vector + SQL)

### src/decision/
Routing and decision validation logic

### src/schemas/
Pydantic data models and types

### src/prompts/
LLM prompt templates and instructions

### api/
FastAPI HTTP server and endpoints

### frontend/
Web UI for chat interface

### data/
Document storage, vector DB, configuration

### tests/
Unit and integration tests

### config/
Application settings and configuration

### docs/
Architecture and setup documentation

### scripts/
Utility scripts for setup and testing

## Data Flow Example

```
User: "Create a report on Q4 sales data"
  ↓
API POST /api/chat
  ↓
Orchestrator LLM decides: "This is a SQL query + Report generation"
  ↓
sql_rag_chain: Generates SQL, executes against database
report_chain: Generates HTML report with results
  ↓
response_synthesizer: Combines results into final response
  ↓
API returns response with report HTML/ID
  ↓
Frontend displays report to user
```

## Configuration

All configuration lives in `config/`:
- `settings.py` - Pydantic settings
- `logging.yaml` - Logging configuration
- `.env.example` - Environment variables template

## Development

See `docs/SETUP.md` for development environment setup and `docs/ARCHITECTURE.md` for detailed component documentation.
