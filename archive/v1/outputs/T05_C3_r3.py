import secrets
import time
import threading
from typing import Dict, Tuple

class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, Tuple[str, float, bool]] = {}
        self._session_duration = 1800
        self._lock = threading.RLock()
    
    def create_session(self, user_id) -> str:
        if not isinstance(user_id, (str, int)):
            raise ValueError("Invalid user_id type")
        if isinstance(user_id, str) and not user_id:
            raise ValueError("Invalid user_id")
        
        session_id = secrets.token_urlsafe(32)
        
        with self._lock:
            self._sessions[session_id] = (str(user_id), time.time(), False)
        
        return session_id
    
    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False
        
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            user_id, creation_time, invalidated = self._sessions[session_id]
            
            if invalidated:
                return False
            
            if time.time() - creation_time > self._session_duration:
                return False
            
            return True
    
    def invalidate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False
        
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            user_id, creation_time, _ = self._sessions[session_id]
            self._sessions[session_id] = (user_id, creation_time, True)
            
            return True
