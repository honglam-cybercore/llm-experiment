import time
import threading

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self.lock = threading.RLock()
    
    def allow_request(self, user_id) -> bool:
        if user_id is None or not isinstance(user_id, (str, int)):
            return False
        
        user_id_str = str(user_id)
        
        if len(user_id_str) > 256:
            return False
        
        with self.lock:
            now = time.time()
            
            if user_id_str not in self.requests:
                self.requests[user_id_str] = (now, 1)
                return True
            
            window_start, count = self.requests[user_id_str]
            
            if now - window_start >= self.window_seconds:
                self.requests[user_id_str] = (now, 1)
                return True
            
            if count < self.max_requests:
                self.requests[user_id_str] = (window_start, count + 1)
                return True
            else:
                return False
