import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def allow_request(self, user_id) -> bool:
        current_time = time.time()
        
        # Remove old requests outside the window
        while self.requests[user_id] and self.requests[user_id][0] <= current_time - self.window_seconds:
            self.requests[user_id].popleft()
        
        # Check if user has exceeded the limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(current_time)
            return True
        else:
            return False
