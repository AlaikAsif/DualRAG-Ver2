# Monitoring Architecture

## Overview
The `monitoring/` module provides **observability, logging, and tracing** for all system components.

**Key Purpose**: Track chain execution, capture metrics, enable debugging and performance analysis.

## Components

### logger.py ✅
**Centralized Logging System**

**Features**:
- Dual output: Console + File (`logs/app.log`)
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging with module context
- Global logger instance accessible throughout system

**Usage**:
```python
from src.monitoring.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing query", extra={"query_id": "q123"})
logger.error("Retrieval failed", exc_info=True)
```

**Log Files**:
- Location: `logs/app.log`
- Format: `[%(asctime)s] %(name)s - %(levelname)s - %(message)s`
- Rotation: Automatic when file grows (max 10 files kept)

### tracer.py ✅
**Execution Tracing & Performance Metrics**

**Decorators**:

1. `@trace_chain_execution(chain_name="static_rag")`
   - Logs chain start/end with timing
   - Captures input/output
   - Records execution duration
   - Handles exceptions gracefully
   - Example:
     ```python
     @trace_chain_execution("rag_retrieval")
     def retrieve_documents(query):
         # ... code ...
     ```

2. `@trace_metrics(component="embeddings")`
   - Tracks performance metrics
   - Records memory usage
   - Captures component-level timings
   - Provides observable data for monitoring

**Metrics Tracked**:
- Execution time (ms)
- Input/output sizes
- Error counts
- Memory consumed
- Throughput (items/sec)

**Example Output**:
```
[Tracer] ✓ static_rag completed in 234.5ms
  Input: {'query': 'What is RAG?', 'k': 3}
  Output: {'response': '...', 'sources': [...]}
```

## Integration Points

### With StaticRAGChain
- `StaticRAGChain.invoke()` decorated with `@trace_chain_execution`
- `_generate_response_with_context()` decorated with `@retry_with_backoff`
- All retrieval operations logged with metadata

### With Schemas
- Every Pydantic model creation logged (via logger)
- Validation errors traceable to source

### With Utils
- Config changes logged
- Retry attempts logged with backoff details

## Metrics Collected

| Component | Metric | Unit |
|-----------|--------|------|
| Retrieval | Documents retrieved | count |
| Retrieval | Average score | 0.0-1.0 |
| Generation | Tokens used | count |
| Generation | Latency | ms |
| Embeddings | Embedding time | ms |
| Embeddings | Vector dim | count |
| Chain | End-to-end time | ms |
| Chain | Error rate | % |

## Best Practices

1. **Log at Boundaries** - Log at function entry/exit for tracing
2. **Include Context** - Add relevant IDs (query_id, session_id, user_id)
3. **Error Logging** - Always log exceptions with `exc_info=True`
4. **Performance** - Use tracer decorators on expensive operations
5. **Cleanup** - Logs auto-rotate, no manual cleanup needed

## Configuration

**Log Level**:
- Set globally: `get_logger().setLevel(logging.DEBUG)`
- Affects all loggers in system
- Persist via environment: `LOG_LEVEL=DEBUG`

**File Location**:
- Configured in `logger.py` (line ~40)
- Default: `logs/app.log`
- Change by modifying `LOG_FILE` constant

## Debug Workflow

```python
# 1. Enable debug logging
get_logger().setLevel(logging.DEBUG)

# 2. Trace execution
@trace_chain_execution("my_chain")
def my_function():
    logger.debug("Step 1: Loading data")
    logger.debug(f"Loaded {len(data)} items")

# 3. Review logs
# Open logs/app.log to see detailed trace
```

## Future Enhancements

- [ ] Metrics aggregation dashboard
- [ ] Real-time alerting on error rates
- [ ] Performance regression detection
- [ ] Cost tracking for LLM calls
- [ ] User satisfaction metrics integration
