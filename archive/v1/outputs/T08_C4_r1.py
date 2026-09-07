import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._user_requests = defaultdict(list)
        self._lock = Lock()
    
    def allow_request(self, user_id) -> bool:
        if user_id is None:
            return False
        
        user_key = str(user_id)
        if not user_key:
            return False
        
        with self._lock:
            now = time.time()
            cutoff_time = now - self.window_seconds
            
            self._user_requests[user_key] = [
                ts for ts in self._user_requests[user_key]
                if ts > cutoff_time
            ]
            
            if len(self._user_requests[user_key]) < self.max_requests:
                self._user_requests[user_key].append(now)
                result = True
            else:
                result = False
            
            if not self._user_requests[user_key]:
                del self._user_requests[user_key]
            
            return result
