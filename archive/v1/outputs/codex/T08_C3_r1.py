import math
import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if isinstance(max_requests, bool) or not isinstance(max_requests, int):
            raise TypeError("max_requests must be an integer")
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")

        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise TypeError("window_seconds must be a number")
        if not math.isfinite(window_seconds) or window_seconds <= 0:
            raise ValueError("window_seconds must be positive and finite")

        self.max_requests = max_requests
        self.window_seconds = float(window_seconds)
        self._requests = {}
        self._lock = threading.Lock()

    def allow_request(self, user_id) -> bool:
        try:
            hash(user_id)
        except Exception:
            return False

        now = time.monotonic()

        with self._lock:
            try:
                timestamps = self._requests.setdefault(user_id, deque())
                cutoff = now - self.window_seconds

                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()

                if len(timestamps) >= self.max_requests:
                    return False

                timestamps.append(now)
                return True
            except Exception:
                return False