# Decision Architecture

## Overview
The `decision/` module handles LLM-based routing decisions and logic validation.

## Components

### router.py
- Main routing orchestration
- Decision flow management
- Fallback routing logic

### validators.py
- Validate LLM routing decisions
- Schema validation
- Safety checks

### parsers.py
- Parse structured LLM output
- JSON parsing
- Error recovery

## Decision Flow
```
LLM Output (routing decision)
      ↓
Validation (is it valid?)
      ↓
Parsing (extract structured data)
      ↓
Route to appropriate chain
```
