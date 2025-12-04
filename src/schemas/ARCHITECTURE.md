# Schemas Architecture

## Overview
The `schemas/` module contains **30+ Pydantic models** for type validation and data structure definition across the entire system.

**Pydantic Benefits**:
- ✅ Automatic data validation (type checking, constraints, ranges)
- ✅ Serialization (convert Python ↔ JSON)
- ✅ Auto-conversion (string "25" → int 25)
- ✅ Self-documenting API (type hints = documentation)
- ✅ IDE autocomplete and error detection

## Core Schema Files

### decisions.py ✅
**LLM Routing & Orchestration Decisions**
- `RoutingDecision` - Main orchestrator decision model
  - `rag_type`: Which RAG system (static/sql/both/none)
  - `needs_report`: Should a report be generated?
  - `response_mode`: How to respond (direct/search_then_answer/clarify/report)
  - `response_confidence`: Confidence level (high/medium/low)
  - `reasoning`: LLM's decision reasoning
- `StaticRagDecision`, `SQLRagDecision`, `ReportDecision` - Sub-decisions
- `ExecutionPlan` - Aggregates decisions with metadata
- `DecisionValidator` - Validation utility
- Enums: `RagType`, `ResponseMode`, `MemoryRequirement`, `QueryIntent`

### rag.py ✅
**Static RAG Request/Response Models**
- `RAGRequest` - User query with parameters
  - `query: str`
  - `retrieval_k: int (1-20)` - Documents to retrieve
  - `use_mmr: bool` - Enable MMR reranking
  - `include_sources: bool` - Include source metadata
- `RAGResponse` - Generated response with sources
  - `response: str` - Generated answer
  - `source_documents: List[SourceDocument]` - Retrieved docs
  - `retrieval_count: int` - How many docs retrieved
- `SourceDocument` - Individual document
  - `content: str` - Document text
  - `metadata: Dict` - Source info (source, page, etc.)
  - `score: float` - Relevance score (0-1)
- `RetrievalResult` - Intermediate retrieval data
- `RAGPipeline` - Configuration schema

### chat.py ✅
**Conversation & Chat Models**
- `ChatMessage` - Single message in conversation
  - `content: str` - Message text
  - `role: MessageRole` - Sender (user/assistant/system)
  - `timestamp: datetime` - When sent
  - `message_id: str` - Unique identifier
- `ChatRequest` - Chat API request
  - `query: str` - Current message
  - `messages: List[ChatMessage]` - Conversation history
  - `user_id: str` - User identifier
  - `session_id: Optional[str]` - Session ID
  - `max_tokens: int` - Response length limit
  - `temperature: float` - Randomness (0-2.0)
- `ChatResponse` - Chat API response
  - `response: str` - Generated message
  - `tokens_used: int` - Tokens consumed
  - `latency_ms: float` - Generation time
- `ConversationHistory` - Full conversation state

### sql.py ✅
**SQL RAG Models**
- `SQLQuery` - SQL to execute
  - `query_string: str` - SQL text
  - `parameters: Dict` - Query parameters
- `SQLResult` - Execution results
  - `rows: List[Dict]` - Result rows
  - `column_names: List[str]` - Column names
  - `row_count: int` - Number of rows
  - `execution_time_ms: float` - Query performance
- `SQLRagRequest` - Natural language to SQL
  - `query: str` - Natural language request
  - `database_context: str` - Available schema
  - `previous_queries: List[str]` - Context
- `SQLRagResponse` - Complete SQL RAG response
  - `original_query: str` - Original NL request
  - `generated_sql: str` - Generated SQL
  - `query_result: SQLResult` - Execution result
  - `interpretation: str` - Results explained
  - `confidence: float` - Generation confidence
- `DatabaseSchema` - Schema information

### followup.py ✅
**Follow-up & Context Models**
- `ConversationContext` - Context from previous turns
  - `last_query: str` - Previous question
  - `interaction_history: List[InteractionContext]` - Past turns
  - `key_entities: Dict` - Important entities
  - `common_topics: List[str]` - Discussion topics
  - `turn_count: int` - Number of turns
- `FollowupAnalysis` - Is this a follow-up?
  - `is_followup: bool`
  - `followup_confidence: float`
  - `related_to_previous: bool`
  - `implicit_context: List[str]` - Implied context
  - `suggested_rag_type: str` - Which RAG to use
- `FollowupRequest` - Follow-up processing request
- `FollowupResponse` - Follow-up analysis result
  - `enriched_query: str` - Query with context resolved
  - `resolved_pronouns: Dict` - Pronoun resolution (it → Q3 sales)

### report.py ✅
**Report Generation Models**
- `ReportSection` - Report section
  - `title: str`
  - `content: str`
  - `subsections: List[ReportSection]`
- `ChartData` - Visualization data
  - `chart_type: ChartType` (line/bar/pie/table/scatter)
  - `title: str`
  - `labels: List[str]`
  - `datasets: List[Dict]` - Data series
- `ReportVisualization` - Chart/visualization element
- `ReportTemplate` - Styling configuration
  - `template_name: str` (default/professional/creative)
  - `color_scheme: Dict`
  - `fonts: Dict`
  - `include_header: bool`
  - `include_toc: bool`
- `Report` - Complete report
  - `metadata: ReportMetadata`
  - `sections: List[ReportSection]`
  - `visualizations: List[ReportVisualization]`
  - `format: ReportFormat` (html/pdf/json/markdown/excel)
- `ReportGenerationRequest` - Report request
- `ReportGenerationResponse` - Generation result with metrics

## Data Validation Example

```python
# Before Pydantic (20+ lines of validation)
def process_request(query, k):
    if not isinstance(query, str):
        raise ValueError("query must be string")
    if len(query) < 1:
        raise ValueError("query too short")
    if not isinstance(k, int):
        raise ValueError("k must be int")
    if k < 1 or k > 20:
        raise ValueError("k must be 1-20")
    # ... more checks

# With Pydantic (1 line!)
request = RAGRequest(query="What is this?", retrieval_k=3)  # ✅ Validated!
```

## Schema Coverage

| Module | Models | Status |
|--------|--------|--------|
| decisions.py | 8+ | ✅ Complete |
| rag.py | 5 | ✅ Complete |
| chat.py | 4 | ✅ Complete |
| sql.py | 5 | ✅ Complete |
| followup.py | 5 | ✅ Complete |
| report.py | 6 | ✅ Complete |
| **Total** | **30+** | **✅ Production Ready** |

## Design Principles

1. **Type Safety** - Catch errors at validation, not at runtime
2. **Self-Documenting** - Type hints serve as API documentation
3. **JSON Ready** - All models serialize/deserialize to JSON automatically
4. **API-First** - Models designed for REST/GraphQL endpoints
5. **Validation at Boundaries** - Validate at every data boundary

## Configuration & Storage

All Pydantic models support:
- `.model_dump()` - Convert to dict
- `.model_dump_json()` - Convert to JSON string
- `.model_validate()` - Parse from dict
- `.model_validate_json()` - Parse from JSON string
- `.model_json_schema()` - Generate JSON schema for API docs

- Documentation through types
- IDE autocomplete support
