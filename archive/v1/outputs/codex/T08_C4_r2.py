import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if isinstance(max_requests, bool) or not isinstance(max_requests, int):
            raise TypeError("max_requests must be an integer")
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise TypeError("window_seconds must be a number")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self._max_requests = max_requests
        self._window_seconds = float(window_seconds)
        self._requests = defaultdict(deque)
        self._lock = threading.Lock()

    def allow_request(self, user_id) -> bool:
        if user_id is None:
            return False

        try:
            hash(user_id)
        except (TypeError, ValueError, Exception):
            return False

        now = time.monotonic()

        with self._lock:
            timestamps = self._requests[user_id]
            cutoff = now - self._window_seconds

            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self._max_requests:
                return False

            timestamps.append(now)
            return True