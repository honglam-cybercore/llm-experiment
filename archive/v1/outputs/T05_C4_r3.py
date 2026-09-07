import secrets
import time
from threading import Lock
from typing import Dict, Tuple, Any


class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, Tuple[Any, float, bool]] = {}
        self._lock = Lock()
        self._session_duration = 30 * 60

    def create_session(self, user_id) -> str:
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[session_id] = (user_id, time.time(), False)
        return session_id

    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False
        with self._lock:
            if session_id not in self._sessions:
                return False
            user_id, creation_time, is_invalidated = self._sessions[session_id]
            if is_invalidated:
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
            user_id, creation_time, is_invalidated = self._sessions[session_id]
            self._sessions[session_id] = (user_id, creation_time, True)
            return True
