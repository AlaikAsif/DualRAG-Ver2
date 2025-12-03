# Schemas Architecture

## Overview
The `schemas/` module contains Pydantic models for type validation and data structures.

## Components

### decisions.py
- **LLM routing decision types**: RoutingDecision (primary model)
- **Decision validation**: Pydantic v2 field_validator and model_validator
- **Routing options enum**: RagType, ResponseMode, MemoryRequirement, etc.
- **Helper models**: StaticRagDecision, SQLRagDecision, ReportDecision, ClarificationDecision, MemoryDecision
- **ExecutionPlan**: Aggregates multiple decisions and metadata
- **DecisionValidator**: Utility for validating decisions before chain execution
- **create_simple_routing_decision()**: Factory for quick decision creation

#### Memory fields (report customization)
- `memory_requirement` (enum): `NONE` (default), `SESSION`, `PERSISTENT`.
- `follow_up_needed` (bool): set to true when a follow-up customization flow is expected.
- `MemoryDecision.context_to_preserve` (list): keys describing what to preserve across follow-up turns (e.g., `['selected_metrics','filters','columns']`).

Design guidance: Memory is opt-in. For the initial implementation, use `SESSION` memory scoped to a `session_id` for report customization flows; persistent cross-session memory can be added later via a storage adapter.

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
