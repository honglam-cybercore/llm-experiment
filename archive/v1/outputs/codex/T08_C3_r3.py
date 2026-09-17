from collections import deque
import math
import threading
import time


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if isinstance(max_requests, bool) or not isinstance(max_requests, int) or max_requests <= 0:
            raise ValueError("max_requests must be a positive integer")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a positive number")
        if not math.isfinite(window_seconds) or window_seconds <= 0:
            raise ValueError("window_seconds must be finite and positive")

        self._max_requests = max_requests
        self._window_seconds = float(window_seconds)
        self._requests = {}
        self._lock = threading.Lock()

    def allow_request(self, user_id) -> bool:
        try:
            hash(user_id)
        except Exception:
            return False

        now = time.monotonic()

        with self._lock:
            timestamps = self._requests.setdefault(user_id, deque())

            while timestamps and now - timestamps[0] >= self._window_seconds:
                timestamps.popleft()

            if len(timestamps) >= self._max_requests:
                return False

            timestamps.append(now)
            return True