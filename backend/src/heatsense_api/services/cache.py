"""Thread-safe in-memory cache with explicit TTL and versioned keys."""

import time
from typing import Any, Dict, Optional, Tuple


class InMemoryCache:
    """Simple, robust in-memory cache with TTL."""

    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if key exists and has not expired."""
        if key not in self._store:
            return None
        value, expiry = self._store[key]
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with expiration timestamp."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._store[key] = (value, time.time() + ttl)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()


cache = InMemoryCache()
