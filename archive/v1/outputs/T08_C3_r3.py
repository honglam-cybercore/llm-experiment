import time
from threading import Lock


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if max_requests <= 0 or window_seconds <= 0:
            raise ValueError("max_requests and window_seconds must be positive")
        
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self._lock = Lock()
    
    def allow_request(self, user_id) -> bool:
        if user_id is None:
            return False
        
        try:
            hash(user_id)
        except TypeError:
            return False
        
        with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            if user_id not in self.requests:
                self.requests[user_id] = []
            
            self.requests[user_id] = [
                timestamp for timestamp in self.requests[user_id]
                if timestamp > window_start
            ]
            
            if len(self.requests[user_id]) >= self.max_requests:
                return False
            
            self.requests[user_id].append(current_time)
            return True
