import secrets
import time
from typing import NamedTuple

class _Session(NamedTuple):
    user_id: str
    creation_time: float
    invalidated: bool

class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._session_timeout = 30 * 60
    
    def create_session(self, user_id) -> str:
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = _Session(
            user_id=str(user_id),
            creation_time=time.time(),
            invalidated=False
        )
        return session_id
    
    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False
        
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        if session.invalidated:
            return False
        
        if time.time() - session.creation_time > self._session_timeout:
            return False
        
        return True
    
    def invalidate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False
        
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        self._sessions[session_id] = _Session(
            user_id=session.user_id,
            creation_time=session.creation_time,
            invalidated=True
        )
        return True
