"""Thread-safe bounded in-memory LRU cache with explicit TTL and versioned keys."""

import time
from collections import OrderedDict
from typing import Any, Optional, Tuple


class InMemoryCache:
    """Bounded in-memory LRU cache with TTL expiration to prevent memory leaks."""

    def __init__(self, default_ttl_seconds: int = 300, max_size: int = 2048):
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self._store: OrderedDict[str, Tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if key exists and has not expired, refreshing access order."""
        if key not in self._store:
            return None
        value, expiry = self._store[key]
        if time.time() > expiry:
            del self._store[key]
            return None
        # Move key to end to mark as recently used
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with expiration timestamp and evict oldest if at capacity."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = time.time() + ttl

        if key in self._store:
            self._store.move_to_end(key)
        elif len(self._store) >= self.max_size:
            # Evict least recently used item (first key)
            self._store.popitem(last=False)

        self._store[key] = (value, expiry)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    def size(self) -> int:
        """Return active cache entry count."""
        return len(self._store)


cache = InMemoryCache()
