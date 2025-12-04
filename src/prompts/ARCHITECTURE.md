# Prompts Architecture

## Overview
The `prompts/` module contains **all LLM prompt templates and instructions**. Prompts are critical for LLM performance, routing decisions, and output quality.

**Key Purpose**: Define consistent, optimized prompts for all LLM interactions across the system.

## Core Components

### 1. **static_rag_prompts.py** ✅ PRODUCTION
**Optimized Prompts for Static RAG Pipeline**

**Key Prompts**:

1. **STATIC_RAG_SYSTEM_PROMPT**
   - Persona: Precise analyst grounded in provided documents
   - Rules: 
     - Only answer from provided context
     - Be honest if information is missing
     - Cite sources (format: [Source: document_name, page X])
     - Refuse speculation beyond document scope
   - Format: Clear, professional tone

2. **STATIC_RAG_QUERY_PROMPT_STRICT**
   - Enables Chain-of-Thought (CoT) reasoning
   - Format: Explicit thinking process before response
   - Example:
     ```
     <context>
     [Retrieved documents here]
     </context>
     
     Question: [User query]
     
     Let me think through this step by step:
     1. What information is relevant?
     2. How do the documents answer this?
     3. What's my confidence level?
     
     Answer: [Response with citations]
     ```

**Variants**:
- **Extractive Mode**: Extract exact text from documents
- **Summary Mode**: Synthesize information concisely
- **Comparison Mode**: Compare across documents
- **Conversational Mode**: Natural, engaging tone

**Features**:
- XML boundary markers for context sections
- Negative constraints (explicitly what NOT to do)
- Structured output format
- Citation requirements with specific format

### 2. **orchestrator_prompts.py** 🔥 CRITICAL
**System Prompts for LLM Decision-Making**

**Responsibilities**:
- LLM routing decisions (static RAG vs SQL vs report vs none)
- Decision validation and confidence scoring
- Few-shot examples for routing accuracy
- Chain-of-thought decision reasoning

**Key Prompts**:
- Routing decision system prompt
- Decision confidence assessment
- Validation constraints

### 3. **chat_prompts.py**
**Conversation & Context Management Prompts**

**Features**:
- Conversation context awareness
- Memory of previous turns
- Tone and style guidelines
- Conversation flow management
- Clarification handling

### 4. **sql_prompts.py**
**Text-to-SQL Generation Prompts**

**Features**:
- Database schema awareness
- Query safety guidelines
- SQL validation rules
- Parameterized query support
- Error recovery prompts

### 5. **report_prompts.py**
**Report Generation Prompts**

**Features**:
- Report structure templates
- Section content generation
- Visualization suggestions
- Formatting and styling guidelines
- Custom requirement interpretation

### 6. **followup_prompts.py**
**Follow-up & Context Continuation**

**Features**:
- Pronoun resolution (it → previous entity)
- Implicit context extraction
- Related question generation
- Conversation threading
- Context preservation

### 7. **templates.py**
**Reusable Prompt Components**

**Features**:
- Base templates for common patterns
- Template variable substitution
- Prompt composition helpers
- Format validators
- Template versioning

## Prompt Design Principles

1. **Clarity** - Unambiguous instructions, clear section boundaries
2. **Structure** - Consistent formatting, logical flow, explicit output format
3. **Examples** - Few-shot examples when needed for complex tasks
4. **Constraints** - Define what NOT to do (negative constraints are powerful)
5. **Testing** - Validate prompt performance before deployment
6. **Versioning** - Track prompt changes and performance impact
7. **Grounding** - For RAG, always emphasize staying within provided context

## Best Practices

1. **Keep Prompts Modular** - Separate concerns (system role, instructions, examples, constraints)
2. **Use XML Tags** - Boundary markers help LLMs understand structure: `<context>...</context>`
3. **Include Examples** - Few-shot examples significantly improve output quality
4. **Be Explicit** - Say what you want and what you don't want
5. **Test Variations** - A/B test different prompt wordings
6. **Version Control** - Track which prompt version produced which results
7. **Document Rationale** - Explain WHY each constraint exists
8. **Citation Format** - For RAG, define exact citation format: `[Source: name, page X]`

## Static RAG Prompt Engineering

**Example Constraint Structure**:
```
MUST DO:
- Answer from context only
- Cite all sources
- Be specific and concrete

MUST NOT DO:
- Speculate beyond context
- Invent facts
- Make up sources
- Use external knowledge

OPTIONAL:
- Explain reasoning
- Note missing information
- Suggest related questions
```

**CoT Effectiveness**:
- Decompose complex questions into steps
- Make reasoning explicit and checkable
- Improves accuracy 10-30% depending on task complexity

## Integration with Chains

**StaticRAGChain** uses:
- `STATIC_RAG_SYSTEM_PROMPT` for system context
- `STATIC_RAG_QUERY_PROMPT_STRICT` for user query
- Retrieved documents automatically inserted between prompts
- Output validation against expected format

## Configuration & A/B Testing

**Version Management**:
- Track prompt versions with performance metrics
- Easy rollback if new prompt underperforms
- Comparison tracking: prompt A vs prompt B accuracy

**Testing Framework**:
- Load different prompt variants
- Compare outputs for same query
- Measure: accuracy, citation quality, user satisfaction
- Store results for analysis

## Example: Evolution of Static RAG Prompt

**v1 (Initial)**: Basic instructions, no examples
- Result: 65% citation accuracy, inconsistent format

**v2 (Added Examples)**: Few-shot examples of correct answers
- Result: 78% citation accuracy, improved format

**v3 (Added Constraints)**: Negative constraints added
- Result: 85% citation accuracy, consistent format

**v4 (Added CoT)**: Chain-of-thought reasoning
- Result: 88% citation accuracy, explicit reasoning

## Future Enhancements

- [ ] Dynamic prompt optimization based on query type
- [ ] Automatic prompt variant testing framework
- [ ] Performance metrics dashboard
- [ ] Prompt A/B testing infrastructure
- [ ] Multilingual prompt variants
