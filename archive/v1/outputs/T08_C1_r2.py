import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def allow_request(self, user_id) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]
        
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(current_time)
            return True
        else:
            return False
