import time
import threading


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60) -> None:
        if not isinstance(max_requests, int) or max_requests <= 0:
            raise ValueError("Invalid max_requests value")
        if not isinstance(window_seconds, int) or window_seconds <= 0:
            raise ValueError("Invalid window_seconds value")
        
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_times = {}
        self._lock = threading.Lock()
    
    def allow_request(self, user_id) -> bool:
        if user_id is None:
            return False
        
        user_id_str = str(user_id)
        if not user_id_str:
            return False
        
        current_time = time.time()
        
        with self._lock:
            if user_id_str not in self._request_times:
                self._request_times[user_id_str] = []
            
            cutoff_time = current_time - self.window_seconds
            self._request_times[user_id_str] = [
                t for t in self._request_times[user_id_str]
                if t > cutoff_time
            ]
            
            if len(self._request_times[user_id_str]) < self.max_requests:
                self._request_times[user_id_str].append(current_time)
                return True
            
            return False
