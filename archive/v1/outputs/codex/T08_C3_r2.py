import heapq
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

        if isinstance(window_seconds, bool):
            raise TypeError("window_seconds must be a positive finite number")
        try:
            window = float(window_seconds)
        except (TypeError, ValueError, OverflowError):
            raise TypeError("window_seconds must be a positive finite number")

        if not math.isfinite(window) or window <= 0:
            raise ValueError("window_seconds must be a positive finite number")

        self._max_requests = max_requests
        self._window_seconds = window
        self._requests = {}
        self._expiry_heap = []
        self._sequence = 0
        self._lock = threading.RLock()

    def allow_request(self, user_id) -> bool:
        if user_id is None:
            return False

        try:
            hash(user_id)
        except (TypeError, ValueError):
            return False

        now = time.monotonic()
        cutoff = now - self._window_seconds

        with self._lock:
            while self._expiry_heap and self._expiry_heap[0][0] <= now:
                _, _, queued_user, _ = heapq.heappop(self._expiry_heap)
                timestamps = self._requests.get(queued_user)

                if not timestamps:
                    continue

                if timestamps[0] <= cutoff:
                    timestamps.popleft()

                if not timestamps:
                    self._requests.pop(queued_user, None)

            timestamps = self._requests.get(user_id)

            if timestamps is None:
                timestamps = deque()
                self._requests[user_id] = timestamps
            else:
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()

                if not timestamps:
                    self._requests.pop(user_id, None)
                    timestamps = deque()
                    self._requests[user_id] = timestamps

            if len(timestamps) >= self._max_requests:
                return False

            timestamps.append(now)
            self._sequence += 1
            heapq.heappush(
                self._expiry_heap,
                (now + self._window_seconds, self._sequence, user_id, now),
            )
            return True