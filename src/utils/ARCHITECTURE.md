# Utils Architecture

## Overview
The `utils/` module contains shared utility functions used across the system.

## Components

### config.py
- Configuration loading
- Environment variable management
- Settings validation

### logging.py
- Logging setup and utilities
- Log formatter
- Handler configuration

### validators.py
- Input validation
- Schema validation
- Error handling

### retry.py
- Retry logic for LLM calls
- Database retry logic
- Exponential backoff

## Best Practices
- Keep utilities focused
- Avoid circular dependencies
- Use consistent patterns
- Document utility parameters
