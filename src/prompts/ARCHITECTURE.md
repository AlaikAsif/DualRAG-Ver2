# Prompts Architecture

## Overview
The `prompts/` module contains all LLM prompt templates and instructions. Prompts are critical for LLM performance and routing decisions.

## Core Components

### 1. **orchestrator_prompts.py** 🔥 CRITICAL
- System prompts for LLM decision-making
- Routing instruction prompts
- Decision validation prompts
- Few-shot examples for routing accuracy

### 2. **chat_prompts.py**
- General conversation prompts
- Context management prompts
- Tone and style guidelines
- Conversation starters

### 3. **static_rag_prompts.py**
- Query reformulation prompts
- Document context prompts
- Relevance ranking prompts
- Synthesis from multiple documents

### 4. **sql_prompts.py**
- Text-to-SQL generation prompts
- Schema awareness prompts
- Query validation prompts
- Safe SQL execution guidelines

### 5. **report_prompts.py**
- Report structure prompts
- Content generation prompts
- Formatting guidelines
- Custom requirement parsing

### 6. **followup_prompts.py**
- Context continuation prompts
- Clarification prompts
- Related question generation
- Conversation threading

### 7. **templates.py**
- Reusable prompt components
- Base templates for common patterns
- Template variables and substitution logic
- Prompt composition helpers

## Prompt Design Principles

1. **Clarity**: Prompts must be unambiguous
2. **Structure**: Use clear formatting and sections
3. **Examples**: Include few-shot examples when needed
4. **Constraints**: Define output format strictly (JSON, etc.)
5. **Versioning**: Track prompt changes for performance

## Best Practices

- Keep prompts modular and reusable
- Test prompt performance before deployment
- Version prompts with performance metrics
- Use structured output formats (JSON)
- Include guardrails and safety constraints

## Configuration
- Prompt version management
- A/B testing framework
- Performance tracking
