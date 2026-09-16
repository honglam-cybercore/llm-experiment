import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(lambda: [0, 0.0])

    def allow_request(self, user_id) -> bool:
        now = time.monotonic()
        count, window_start = self._requests[user_id]

        if now - window_start >= self.window_seconds:
            count = 0
            window_start = now

        if count >= self.max_requests:
            return False

        self._requests[user_id] = [count + 1, window_start]
        return True