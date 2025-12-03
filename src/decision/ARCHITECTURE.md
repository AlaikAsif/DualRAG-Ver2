# Decision Architecture

## Overview
The `decision/` module handles intelligent routing decisions using a multi-stage approach:
1. **LLM-based routing** (primary): Uses structured function calling for precise decisions
2. **Semantic fallback** (secondary): Uses embeddings + cosine similarity for robustness
3. **Validation & parsing**: Ensures decisions are valid and well-formed

## Components

### router.py
- **Multi-stage routing orchestration**
  - Primary: LLM-based decision via structured output (function calling)
  - Secondary: Semantic similarity routing using embeddings as fallback
  - Tertiary: Default fallback logic (static routing)
- **Decision confidence scoring**
- **Fallback chain selection**
- Routes queries to: static RAG, SQL RAG, chat, reports, followup chains

### validators.py
- Validate LLM routing decisions against RoutingDecision schema
- Type and field validation (Pydantic v2)
- Safety checks (confidence thresholds, fallback triggers)
- ExecutionPlan validation

### parsers.py
- Parse structured LLM output from function calling
- Handle partial or malformed decisions gracefully
- Extract confidence scores and reasoning
- Error recovery with sensible defaults

## Routing Strategy

### Stage 1: LLM-Based Routing (Primary)
```
User Query
    ↓
[LLM with RoutingDecision schema]
    ↓
Extract structured fields:
  - rag_type (static/sql/none)
  - needs_static_rag, needs_sql_rag
  - report_type, response_mode
  - response_confidence
    ↓
Validate decision
    ↓
If confidence >= threshold → route to chain
```

### Stage 2: Semantic Fallback (Confidence < Threshold)
```
User Query
    ↓
[Embed query using sentence-transformers]
    ↓
[Compare similarity to prompt templates]
  (static_rag_template, sql_rag_template, chat_template, etc.)
    ↓
Select chain with highest similarity
    ↓
Construct RoutingDecision with confidence score
```

### Stage 3: Static Fallback
```
If both Stage 1 & 2 fail:
  → Route to general chat chain
  → Log decision and uncertainty
```

## Decision Flow
```
User Query
      ↓
┌────────────────────────────────────────────┐
│  Stage 1: LLM Structured Routing           │
│  (function calling + RoutingDecision)      │
└────────────────────────────────────────────┘
      ↓ (Success & high confidence)
  [Validate & Parse]
      ↓
  [Route to Chain]
      ↓ (Low confidence or error)
┌────────────────────────────────────────────┐
│  Stage 2: Semantic Fallback                │
│  (embeddings + cosine similarity)          │
└────────────────────────────────────────────┘
      ↓
  [Construct Decision]
      ↓
  [Route to Chain]
      ↓ (All fail)
┌────────────────────────────────────────────┐
│  Stage 3: Static Fallback                  │
│  (default to chat chain)                   │
└────────────────────────────────────────────┘
```

## RoutingDecision Schema
See `src/schemas/decisions.py` for full schema.

**Key Fields:**
- `rag_type`: Enum [static_rag, sql_rag, none]
- `needs_static_rag`, `needs_sql_rag`: Bool flags
- `static_rag_query`, `sql_intent`: Query specifications
- `response_confidence`: Float [0.0-1.0] (used for fallback decision)
- `response_mode`: Enum [direct, rag, hybrid]
- `reasoning`: String explanation of the decision
 
## Memory (report customization)

- `memory_requirement`: Enum [NONE, SESSION, PERSISTENT]. Default `NONE` — memory is opt-in.
- `follow_up_needed`: Bool. When true and `memory_requirement` is `SESSION` or `PERSISTENT`, the follow-up flow may persist selective context.
- `MemoryDecision.context_to_preserve`: List of context keys to save for follow-up (e.g., `['selected_metrics', 'filters', 'columns']`).

Design note: for now, memory is intended primarily for session-scoped report customization follow-ups — the followup chain will load saved context for the same `session_id` and pre-fill customization prompts. Persistent cross-session memory is supported conceptually but optional and requires a storage adapter.
