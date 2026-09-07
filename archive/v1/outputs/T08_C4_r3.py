import time
import threading
from typing import Any, Dict, Tuple

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        if not isinstance(max_requests, int) or max_requests <= 0:
            raise ValueError("max_requests must be a positive integer")
        if not isinstance(window_seconds, int) or window_seconds <= 0:
            raise ValueError("window_seconds must be a positive integer")
        
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._user_requests: Dict[Any, Tuple[int, float]] = {}
        self._lock = threading.Lock()
    
    def allow_request(self, user_id: Any) -> bool:
        if user_id is None:
            return False
        
        try:
            hash(user_id)
        except TypeError:
            return False
        
        current_time = time.time()
        
        with self._lock:
            if user_id not in self._user_requests:
                self._user_requests[user_id] = (1, current_time)
                return True
            
            request_count, window_start = self._user_requests[user_id]
            
            if current_time - window_start >= self.window_seconds:
                self._user_requests[user_id] = (1, current_time)
                return True
            
            if request_count < self.max_requests:
                self._user_requests[user_id] = (request_count + 1, window_start)
                return True
            
            return False