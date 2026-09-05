"""
InsightInMinutes - Optimized Caching Engine
Provides normalized exact and fuzzy content hashing to eliminate redundant Gemini API calls,
prevent quota exhaustion, and deliver instant sub-second response times.
"""

from __future__ import annotations
import hashlib
import re
import time
from typing import Any, Dict, Optional


def normalize_text(text: str) -> str:
    """Lowercase, strip non-alphanumeric chars, and collapse whitespace."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def generate_cache_key(content_or_url: str, min_words: int, max_words: int) -> str:
    """Generates a stable, collision-resistant SHA-256 hash for article queries."""
    normalized = normalize_text(content_or_url)
    raw_key = f"{normalized[:5000]}|{min_words}|{max_words}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]


class NewsSummaryCache:
    """
    In-memory session response cache with hit tracking and metadata storage.
    Prevents redundant calls to Gemini when summarizing the same or similar article text.
    """

    def __init__(self, max_entries: int = 200):
        self.max_entries = max_entries
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a cached record if present."""
        if key in self._cache:
            self.hits += 1
            record = self._cache[key]
            record["last_accessed"] = time.time()
            return record
        self.misses += 1
        return None

    def set(self, key: str, record: Dict[str, Any]) -> None:
        """Stores a record, evicting the oldest entry if max_entries is exceeded."""
        if len(self._cache) >= self.max_entries:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].get("last_accessed", 0))
            self._cache.pop(oldest_key, None)
        record["last_accessed"] = time.time()
        self._cache[key] = record

    def clear(self) -> None:
        """Flushes the cache."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0


# Singleton global cache instance
_global_cache = NewsSummaryCache()


def get_cache() -> NewsSummaryCache:
    """Returns the shared cache instance."""
    return _global_cache
