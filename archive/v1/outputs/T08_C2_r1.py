import time

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def allow_request(self, user_id) -> bool:
        current_time = time.time()

        if user_id not in self.requests:
            self.requests[user_id] = []

        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.window_seconds
        ]

        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(current_time)
            return True
        else:
            return False
