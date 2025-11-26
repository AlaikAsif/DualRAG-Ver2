# LLM Orchestration Guide

## Overview

The **Orchestrator** is the heart of this chatbot system. It's an LLM that makes ALL routing decisions about what action to take based on user input.

## How It Works

### Decision Flow

```
User Input
    ↓
Get conversation context (history, previous decisions)
    ↓
Send to Orchestrator LLM with routing prompt
    ↓
LLM analyzes intent and returns structured decision:
    ├─ action: "chat" | "static_rag" | "sql_rag" | "report" | "followup"
    ├─ confidence: 0.0-1.0
    ├─ reasoning: explanation of decision
    └─ parameters: action-specific parameters
    ↓
Validate decision (schema, confidence threshold)
    ↓
Route to appropriate chain
    ↓
Execute chain and get results
    ↓
Response synthesizer combines results
    ↓
Return to user
```

## Routing Decisions

### 1. **Chat** (`action: "chat"`)
- User asks a general knowledge question
- No external data needed
- LLM can answer directly

Example: "What is Python?"
Response: Direct LLM response

### 2. **Static RAG** (`action: "static_rag"`)
- User asks about document content
- Need to search knowledge base
- Retrieve and synthesize from documents

Example: "What does chapter 3 say about..."
Response: Synthesized from retrieved documents

### 3. **SQL RAG** (`action: "sql_rag"`)
- User asks for data from database
- Need text-to-SQL conversion
- Execute query and format results

Example: "Show me sales by region"
Response: Query results formatted as text/table

### 4. **Report** (`action: "report"`)
- User requests structured report
- Often combined with SQL or Static RAG
- Generate HTML/PDF report

Example: "Create a Q4 report"
Response: HTML report with data

### 5. **Follow-up** (`action: "followup"`)
- User asks clarification on previous response
- Need conversation context
- Build on previous results

Example: "Tell me more about..."
Response: Context-aware continuation

## Prompt Strategy

### System Prompt
Sets the orchestrator's role and instructions:
- Decision options
- When to use each
- Output format requirements
- Safety guidelines

### Few-Shot Examples
Include examples of each decision type to improve accuracy:
```
User: "What's the weather?"
Decision: {"action": "chat", "confidence": 0.95, ...}

User: "Show sales by product"
Decision: {"action": "sql_rag", "confidence": 0.9, ...}

User: "Summarize chapter 2"
Decision: {"action": "static_rag", "confidence": 0.88, ...}
```

### Context
Provide relevant context:
- Available documents
- Database tables
- Previous conversation
- User preferences

## Confidence and Fallback

Each decision includes a confidence score (0.0-1.0).

**If confidence < threshold (default 0.7)**:
- Try fallback action (usually "chat")
- Log low-confidence decision
- Monitor for patterns

## Performance Metrics

Track routing accuracy:
- % of decisions that led to correct result
- Response satisfaction
- False positives/negatives per action type
- Decision latency

## Improving Routing

1. **Refine Prompts**: Adjust system prompt and examples
2. **Add Context**: Include more relevant information
3. **Test Decisions**: A/B test routing logic
4. **Monitor Patterns**: Identify low-confidence areas
5. **User Feedback**: Incorporate feedback into system prompt

## Advanced Features

### Multi-Step Decisions
Some queries may require multiple actions:
```
User: "Create a report on Q4 sales by region"
Step 1: Decide "sql_rag" (get data)
Step 2: Decide "report" (format results)
Step 3: Synthesize both results
```

### Dynamic Prompts
Adjust prompt based on:
- User preferences
- Available documents/databases
- Time of day or context
- User history

### Confidence Thresholds
Different thresholds per action type:
- "chat": 0.6 (low bar, can always fallback)
- "static_rag": 0.75 (medium)
- "sql_rag": 0.85 (high - query execution is risky)
- "report": 0.8 (high - complex generation)

## Testing

Manual testing of orchestrator:
```bash
python scripts/test_orchestrator.py
```

Run routing accuracy tests:
```bash
pytest tests/integration/test_llm_decisions.py -v
```

## Troubleshooting

### Wrong routing decisions
1. Check prompt wording
2. Add more examples
3. Increase context
4. Check confidence threshold

### Inconsistent decisions
1. Use deterministic seed
2. Simplify decision options
3. Add explicit constraints
4. Use structured output (JSON)

### Performance issues
1. Cache orchestrator responses
2. Use smaller model for routing
3. Batch decisions
4. Profile latency per step
