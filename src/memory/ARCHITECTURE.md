# Memory Module Architecture

## Purpose

The `memory/` package provides a pluggable memory subsystem used by chains to store short-lived
session and conversation state (follow-ups, small embeddings, temporary context). The current
implementation is a simple, thread-safe in-memory store intended for development and local testing.

## Components

- `in_memory.py` — Main implementation:
  - `MemoryStore` class: a dictionary-backed store keyed by `session_id` → `namespace` → `key`.
  - Thread-safety: uses a `threading.Lock` to protect concurrent access.
  - TTL support: `save(..., ttl=seconds)` stores an `expires_at` timestamp and expired keys are
    cleaned on access (`load` / `get_all`).
  - Public API:
    - `save(session_id, namespace, key, value, ttl=None)` — store a value.
    - `load(session_id, namespace, key)` — retrieve a value or `None` if missing/expired.
    - `get_all(session_id, namespace)` — return dict of non-expired key→value pairs.
    - `delete(session_id, namespace, key)` — remove an entry.

## Design Rationale

- Simplicity: the in-memory store has minimal dependencies and predictable semantics for local
development, CI, and testing.
- Thread-safety: locking avoids race conditions when multiple threads in the same process access
  memory concurrently (typical in synchronous web servers).
- Extensibility: the package is designed to be swapped with a persistent adapter (Redis,
  SQLite, or cloud-backed) by implementing the same API surface. A factory/DI layer in the
  application can choose the appropriate adapter at runtime.

## Usage Patterns

- Short-lived session state: store small objects like follow-up intents, temporary flags, or
  last-seen message IDs.
- Not for large data: do not store large blobs or the full conversation history here — prefer
  persistent stores or chunked storage.
- TTL semantics: use `ttl` for expiring ephemeral items automatically.

## Migration to persistent stores

To move from `MemoryStore` to a persistent backend:
- Implement the same API methods (`save`, `load`, `get_all`, `delete`) backed by the chosen
  storage engine.
- Provide a factory function or dependency-injection entrypoint so chains can request the
  configured memory adapter.
- Ensure TTL semantics are implemented or emulated by the adapter.

## Tests

- Include unit tests that validate concurrency behavior, TTL expiry, and API contract.

