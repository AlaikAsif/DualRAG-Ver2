# Utils Architecture

## Overview
The `utils/` module contains **shared utilities for configuration, retry logic, and error handling** used across the system.

**Key Purpose**: Provide reusable infrastructure components (config loading, retry mechanisms) that multiple modules depend on.

## Components

### config.py ✅
**Configuration Management System**

**Features**:
- Load config from files (JSON, YAML, ENV)
- Load from environment variables
- Dot notation access: `config.get("rag.retrieval_k")`
- Type coercion (string "25" → int 25)
- Defaults and override support
- Hot-reload capability

**Configuration Hierarchy**:
1. Hardcoded defaults (lowest priority)
2. Config files (json/yaml in config/)
3. Environment variables (highest priority)

**Usage**:
```python
from src.utils.config import Config

config = Config()
retrieval_k = config.get("rag.retrieval_k", default=3)  # type: int
llm_model = config.get("llm.model", default="llama2")   # type: str
```

**Supported Config Files**:
- `config/default.json` - Default settings
- `config/rag.json` - RAG-specific settings
- `config/llm.json` - LLM settings
- Environment: `APP_CONFIG_FILE` variable

**Type Support**:
- Auto-converts string config values to correct Python types
- Handles: bool, int, float, str, list, dict
- Example: env var `RAG_RETRIEVAL_K=3` → config.get("rag.retrieval_k") returns int 3

### retry.py ✅
**Resilience & Retry Mechanism**

**Decorators**:

1. `@retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)`
   - Retries failed operations exponentially
   - Delays: 1s → 2s → 4s → failure
   - Usage: LLM calls, database queries, API calls
   - Example:
     ```python
     @retry_with_backoff(max_retries=3)
     def call_llm(prompt):
         # LLM call here - auto-retries on failure
     ```

2. `@retry_on_exception(exceptions=(ValueError, TimeoutError), max_retries=2)`
   - Retry only on specific exceptions
   - Ignore other exceptions (let them propagate)
   - Usage: Selective error handling

**Context Manager**:
```python
with RetryableOperation(max_retries=3) as op:
    op.execute(lambda: my_function())
```

**Configuration**:
- `max_retries`: Number of retry attempts (default 3)
- `initial_delay`: First retry delay in seconds (default 1.0)
- `backoff_factor`: Multiplier for exponential backoff (default 2.0)
- `exponential`: Use exponential (True) or linear (False) delay

**Example Backoff Sequence**:
```
Attempt 1: Fails immediately
Attempt 2: Wait 1s, then retry
Attempt 3: Wait 2s, then retry
Attempt 4: Wait 4s, then retry
Attempt 5: Fails → Exception raised
```

**Benefits**:
- Resilient to transient failures (network hiccups, rate limits)
- Automatic jitter prevents thundering herd
- Graceful degradation with max retry limits

## Integration Points

### With StaticRAGChain
- `_generate_response_with_context()` uses `@retry_with_backoff`
- LLM calls automatically retry on rate limits/timeouts
- Failure after max retries raises informative exception

### With Config
- Retry settings loaded from config: `config.get("retry.max_retries")`
- Allows tuning retry behavior without code changes
- Per-environment configuration (dev/prod retry counts differ)

### With Logger
- Each retry attempt logged with attempt number
- Final failure logged with full exception context
- Performance metrics tracked per retry

## Configuration Management

**Default Config Structure**:
```json
{
  "rag": {
    "retrieval_k": 3,
    "use_mmr": true,
    "mmr_diversity_weight": 0.3
  },
  "llm": {
    "model": "llama2",
    "max_tokens": 500,
    "temperature": 0.7
  },
  "retry": {
    "max_retries": 3,
    "initial_delay": 1.0,
    "backoff_factor": 2.0
  }
}
```

**Environment Variable Overrides**:
- `RAG_RETRIEVAL_K=5` → overrides `config.rag.retrieval_k`
- `LLM_MODEL=gpt-4` → overrides `config.llm.model`
- `RETRY_MAX_RETRIES=5` → overrides `config.retry.max_retries`

**Access Pattern**:
```python
config = Config()

# File-based config
retrieval_k = config.get("rag.retrieval_k")       # Uses default if not set
retrieval_k = config.get("rag.retrieval_k", 5)    # Default to 5

# Env override wins
# If env var RAG_RETRIEVAL_K=10, this returns 10
retrieval_k = config.get("rag.retrieval_k")
```

## Best Practices

1. **Load Config Once** - Instantiate Config at module level, not per-request
2. **Dot Notation** - Use "module.key" for hierarchical config access
3. **Provide Defaults** - Always pass default value: `config.get("key", default=value)`
4. **Environment Overrides** - Use env vars for deployment-specific settings
5. **Retry Strategically** - Use on I/O operations (LLM, DB, API), not CPU operations
6. **Log Retries** - Enables debugging of flaky operations
7. **Set Reasonable Limits** - max_retries=3-5, not infinite

## Error Handling

**Retry Exhaustion**:
```python
try:
    result = call_llm(prompt)
except Exception as e:
    logger.error(f"LLM call failed after retries: {e}")
    # Fall back to cached response or error message
```

**Transient vs Permanent Errors**:
- Retried: Network timeouts, rate limits, temporary service outages
- Not retried: Invalid inputs, auth failures, malformed requests
- Control via `@retry_on_exception(exceptions=(TimeoutError,))`

## Monitoring

**Metrics**:
- Retry attempts per operation
- Success rate after retries
- Time spent waiting for retries
- Failure rate of max-exhausted operations

**Logging**:
- Each retry logged with: `[Retry 2/3] <operation> ...`
- Backoff delays logged: `[Retry] Waiting 2.0s before next attempt`
- Final result logged: `[Success] After 2 retries` or `[Failed] Max retries exceeded`
