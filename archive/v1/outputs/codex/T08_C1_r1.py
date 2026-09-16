import time
import threading
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(deque)
        self._lock = threading.Lock()

    def allow_request(self, user_id) -> bool:
        now = time.monotonic()

        with self._lock:
            requests = self._requests[user_id]

            while requests and now - requests[0] >= self.window_seconds:
                requests.popleft()

            if len(requests) >= self.max_requests:
                return False

            requests.append(now)
            return True