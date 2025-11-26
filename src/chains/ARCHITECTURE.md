# Chains Architecture

## Overview
The `chains/` module contains the core LLM interaction logic and chain orchestration. This is where conversation flow, routing decisions, and response synthesis happen.

## Core Components

### 1. **llm.py** - LLM Initialization
- Initialize Ollama (or other LLM providers)
- Manage LLM connection pooling
- Handle model loading and configuration

### 2. **orchestrator.py** 🔥 MAIN
- **Primary decision-maker** for routing requests
- LLM analyzes user intent and decides which chain to execute:
  - Direct chat response
  - Static RAG (knowledge base search)
  - SQL RAG (database query)
  - Report generation
  - Follow-up handling
- Implements intelligent fallback logic
- Validates routing decisions

### 3. **chat_chain.py**
- Handles conversational interactions
- Maintains conversation context
- Implements turn-taking logic
- Manages chat history

### 4. **static_rag_chain.py**
- Reformulates user queries for document search
- Retrieves relevant documents from vector store
- Ranks retrieved documents
- Passes results to response synthesizer

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
- LangChain (for chain management)
- Ollama (LLM provider)
- Prompts module (for prompt templates)

## Configuration
- LLM model selection
- Temperature and other LLM parameters
- Chain-specific settings (timeouts, retries)
