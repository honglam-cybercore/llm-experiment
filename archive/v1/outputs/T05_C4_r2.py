import secrets
import time
from threading import Lock

class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._session_timeout = 30 * 60  # 30 minutes in seconds
        self._lock = Lock()
    
    def create_session(self, user_id) -> str:
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        session_id = secrets.token_urlsafe(32)
        
        with self._lock:
            self._sessions[session_id] = {
                'user_id': user_id,
                'created_at': time.time(),
                'invalidated': False
            }
        
        return session_id
    
    def validate_session(self, session_id) -> bool:
        if not session_id:
            return False
        
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            session = self._sessions[session_id]
            
            if session['invalidated']:
                return False
            
            current_time = time.time()
            if current_time - session['created_at'] > self._session_timeout:
                return False
        
        return True
    
    def invalidate_session(self, session_id) -> bool:
        if not session_id:
            return False
        
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            self._sessions[session_id]['invalidated'] = True
        
        return True
