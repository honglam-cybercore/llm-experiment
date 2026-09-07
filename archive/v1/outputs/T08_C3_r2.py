import time
import threading
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
    
    def allow_request(self, user_id) -> bool:
        try:
            hash(user_id)
        except TypeError:
            raise TypeError("user_id must be hashable")
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        with self._lock:
            self._requests[user_id] = [
                ts for ts in self._requests[user_id]
                if ts > window_start
            ]
            
            if len(self._requests[user_id]) < self.max_requests:
                self._requests[user_id].append(current_time)
                return True
            
            return False
