"""
InsightInMinutes - Device & Session Rate Limiter
Modeled after anzum.ai protection architecture.
Prevents rapid button spamming, quota exhaustion, and runaway API costs.
"""

from __future__ import annotations
import time
from typing import Dict, List, Tuple

# Configuration
MIN_REQUEST_INTERVAL_SECONDS = 2.5   # Debounce rapid clicks
MAX_REQUESTS_PER_MINUTE = 8          # Rolling 1-minute window
MAX_SESSION_REQUESTS = 60            # Maximum queries per session


class RateLimiter:
    """
    Session rate limiter tracking activity timestamps.
    Enforces debounce intervals and sliding window request caps.
    """

    def __init__(
        self,
        min_interval_sec: float = MIN_REQUEST_INTERVAL_SECONDS,
        max_rpm: int = MAX_REQUESTS_PER_MINUTE,
        max_session: int = MAX_SESSION_REQUESTS,
    ):
        self.min_interval = min_interval_sec
        self.max_rpm = max_rpm
        self.max_session = max_session
        self._last_request_time: Dict[str, float] = {}
        self._request_history: Dict[str, List[float]] = {}
        self._session_counts: Dict[str, int] = {}

    def check_rate_limit(self, session_id: str = "default") -> Tuple[bool, str]:
        """
        Validates whether a request from the given session is permitted.

        Returns:
            (allowed: bool, message: str)
        """
        now = time.time()

        # 1. Check debounce interval
        last_time = self._last_request_time.get(session_id, 0.0)
        elapsed = now - last_time
        if elapsed < self.min_interval:
            wait_time = round(self.min_interval - elapsed, 1)
            return (
                False,
                f"Please wait {wait_time}s before generating another brief.",
            )

        # 2. Check total session cap
        count = self._session_counts.get(session_id, 0)
        if count >= self.max_session:
            return (
                False,
                "Session limit reached (60 summaries). Please refresh the workspace to start a new session.",
            )

        # 3. Check sliding window RPM (rolling 60 seconds)
        history = self._request_history.get(session_id, [])
        cutoff = now - 60.0
        history = [t for t in history if t > cutoff]
        if len(history) >= self.max_rpm:
            earliest = history[0]
            cooldown = max(1, int(60.0 - (now - earliest)))
            return (
                False,
                f"Rate limit reached ({self.max_rpm} requests/min). Please wait {cooldown}s.",
            )

        # Update metrics
        history.append(now)
        self._request_history[session_id] = history
        self._last_request_time[session_id] = now
        self._session_counts[session_id] = count + 1

        return True, ""

    def reset_session(self, session_id: str = "default") -> None:
        """Resets tracking for the given session."""
        self._last_request_time.pop(session_id, None)
        self._request_history.pop(session_id, None)
        self._session_counts.pop(session_id, None)


# Global singleton instance
_global_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Returns the shared rate limiter instance."""
    return _global_limiter
