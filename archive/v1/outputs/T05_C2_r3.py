import uuid
import time

class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
    
    def create_session(self, user_id) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = (user_id, time.time(), False)
        return session_id
    
    def validate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False
        
        user_id, created_at, invalidated = self._sessions[session_id]
        
        if invalidated:
            return False
        
        if time.time() - created_at > 1800:
            return False
        
        return True
    
    def invalidate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False
        
        user_id, created_at, _ = self._sessions[session_id]
        self._sessions[session_id] = (user_id, created_at, True)
        return True
