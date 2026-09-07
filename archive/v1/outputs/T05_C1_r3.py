import uuid
from datetime import datetime, timedelta


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
    
    def create_session(self, user_id) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'invalidated': False
        }
        return session_id
    
    def validate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        if session['invalidated']:
            return False
        
        if datetime.now() - session['created_at'] > timedelta(minutes=30):
            return False
        
        return True
    
    def invalidate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False
        
        self._sessions[session_id]['invalidated'] = True
        return True
