"""Simple in-memory MemoryStore for session-scoped follow-ups.

API:
- save(session_id, namespace, key, value, ttl=None)
- load(session_id, namespace, key)
- get_all(session_id, namespace)
- delete(session_id, namespace, key)

Thread-safe and intended for development/testing. Persistent adapters
(e.g., SQLite or Redis) can be added later.
"""
from typing import Any, Dict, Optional
import threading
import time

class MemoryStore:
    def __init__(self):
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def save(self, session_id: str, namespace: str, key: str, value: Any, ttl: Optional[int] = None):
        """Save a value under session_id/namespace/key. ttl is seconds."""
        with self._lock:
            ns = self._store.setdefault(session_id, {}).setdefault(namespace, {})
            expires_at = time.time() + ttl if ttl else None
            ns[key] = {"value": value, "expires_at": expires_at}

    def load(self, session_id: str, namespace: str, key: str) -> Optional[Any]:
        with self._lock:
            ns = self._store.get(session_id, {}).get(namespace, {})
            item = ns.get(key)
            if not item:
                return None
            if item["expires_at"] and item["expires_at"] < time.time():
                # expired
                del ns[key]
                return None
            return item["value"]

    def get_all(self, session_id: str, namespace: str) -> Dict[str, Any]:
        with self._lock:
            ns = self._store.get(session_id, {}).get(namespace, {})
            result = {}
            for k, v in list(ns.items()):
                if v["expires_at"] and v["expires_at"] < time.time():
                    del ns[k]
                    continue
                result[k] = v["value"]
            return result

    def delete(self, session_id: str, namespace: str, key: str):
        with self._lock:
            ns = self._store.get(session_id, {}).get(namespace, {})
            ns.pop(key, None)
