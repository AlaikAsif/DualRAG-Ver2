# Chains Architecture

## Overview
The `chains/` module contains the core LLM interaction logic and chain orchestration. This is where conversation flow, routing decisions, and response synthesis happen.

## Core Components

### 1. **llm.py** - LLM Initialization
- Initialize Ollama (or other LLM providers)
- Manage LLM connection pooling
- Handle model loading and configuration

### 2. **orchestrator.py** 🔥 MAIN
- **Primary decision-maker** for routing requests using multi-stage approach
- **Stage 1 - LLM-Based Routing** (primary):
  - Uses RoutingDecision structured output (function calling)
  - LLM analyzes user intent and decides which chain to execute:
    - Direct chat response
    - Static RAG (knowledge base search)
    - SQL RAG (database query)
    - Report generation
    - Follow-up handling
  - Extracts confidence score for fallback decisions
- **Stage 2 - Semantic Fallback** (if low confidence):
  - Embeds query using sentence-transformers
  - Compares similarity to chain prompt templates
  - Routes to most similar chain
- **Stage 3 - Static Fallback** (if both fail):
  - Routes to general chat chain with logging
- Implements intelligent fallback chain selection
- Validates routing decisions via DecisionValidator

### 3. **chat_chain.py**
- Handles conversational interactions
- Maintains conversation context
- Implements turn-taking logic
- Manages chat history

### 4. **static_rag_chain.py** ✨ NEW
- **Full static RAG pipeline** for document-augmented response generation
- **Workflow**:
  1. Load persisted FAISS vector index from disk
  2. Retrieve relevant documents using MMR (Maximal Marginal Relevance) reranking
  3. Format retrieved context for LLM consumption
  4. Generate response with strict RAG prompts (CoT-enabled, no hallucination)
  5. Track metrics and log execution details
- **Key Features**:
  - MMR reranking for diverse document selection
  - Configurable retrieval_k (1-20) and initial_k for reranking
  - Strict RAG prompts with XML-tagged context boundaries
  - Automatic LLM retry with exponential backoff
  - Source document tracking with metadata preservation
  - Batch retrieval support for multiple queries
  - Pydantic schema validation (RAGRequest, RAGResponse)
- **Integration**: Returns RAGResponse with response text + source documents + retrieval metrics

### 5. **sql_rag_chain.py**
- Converts natural language to SQL queries
- Handles database schema awareness
- Executes queries safely
- Formats database results for synthesis

### 6. **report_chain.py**
- Generates HTML/PDF reports
- Supports custom report layouts
- Integrates RAG results into report format
- Handles report styling and templates

### 7. **followup_chain.py**
- Handles follow-up questions based on previous context
- Manages conversation threading
- Implements clarification logic

### 8. **response_synthesizer.py**
- Combines multiple RAG/chain results
- Generates coherent final response
- Formats output for frontend
- Ensures response consistency

## Data Flow

```
User Input
    ↓
orchestrator.py (LLM routing decision)
    ↓
├── Static RAG? → static_rag_chain.py → vector search
├── SQL Query? → sql_rag_chain.py → database query
├── Report? → report_chain.py → report generation
├── Chat? → chat_chain.py → conversation handling
└── Follow-up? → followup_chain.py → context-aware response
    ↓
response_synthesizer.py (combines all results)
    ↓
Final Response to User
```

## Key Design Decisions

1. **LLM-Driven Orchestration**: The LLM makes ALL routing decisions, not hard-coded rules
2. **Modular Chains**: Each chain is independent and testable
3. **Response Synthesis**: Final response is constructed from all available context
4. **Error Handling**: Each chain has built-in fallback mechanisms

## Dependencies
- **LangChain** (chain management)
- **Ollama** (LLM provider)
- **Prompts module** (prompt templates)
- **Schemas module** (Pydantic models for type safety)
- **Monitoring module** (logging, tracing, metrics)
- **Utils module** (config, retry logic)
- **RAG modules** (static/sql retrieval)
- **FAISS** (vector search for static RAG)
- **sentence-transformers** (embeddings for static RAG)

## Configuration
- LLM model selection
- Temperature and other LLM parameters
- Chain-specific settings (timeouts, retries)

## Implementation Status

### ✅ Completed & Tested
- **static_rag_chain.py** - Full implementation with FAISS integration, MMR reranking, strict prompts
- **llm.py** - Ollama initialization and connection management
- **orchestrator.py** - Multi-stage routing with fallback logic
- **Monitoring Infrastructure** - Logger, tracer, metrics collection
- **Pydantic Schemas** - Type validation for all data structures
- **Integration Tests** - Full end-to-end pipeline validation (9/9 tests passing)

### 🔄 In Progress / Ready for Integration
- **chat_chain.py** - Conversation handling (needs memory integration)
- **sql_rag_chain.py** - Database query handling (schema management ready)
- **report_chain.py** - Report generation framework
- **followup_chain.py** - Follow-up question handling (context preservation)
- **response_synthesizer.py** - Result aggregation and formatting

### Data Structures
All chains use **Pydantic models** for input/output validation:
- `RAGRequest` / `RAGResponse` (static RAG)
- `ChatRequest` / `ChatResponse` (conversations)
- `SQLRagRequest` / `SQLRagResponse` (database queries)
- `FollowupRequest` / `FollowupResponse` (context-aware follow-ups)
- `ReportGenerationRequest` / `ReportGenerationResponse` (reports)
- `RoutingDecision` (orchestrator decisions)

