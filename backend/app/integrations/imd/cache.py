import time
from typing import Any, Optional, Dict

class IMDCache:
    def __init__(self, default_ttl_seconds: int = 900):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["data"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl_to_use = ttl if ttl is not None else self.default_ttl
        self._cache[key] = {
            "data": value,
            "expires_at": time.time() + ttl_to_use,
            "created_at": time.time()
        }

    def clear(self) -> None:
        self._cache.clear()

imd_cache = IMDCache()
