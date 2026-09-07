import secrets
import time
from typing import Any


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._session_timeout = 30 * 60

    def create_session(self, user_id) -> str:
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = {
            'user_id': user_id,
            'created_at': time.time(),
            'invalidated': False
        }
        return session_id

    def validate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]

        if session['invalidated']:
            return False

        elapsed_time = time.time() - session['created_at']
        if elapsed_time > self._session_timeout:
            return False

        return True

    def invalidate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False

        self._sessions[session_id]['invalidated'] = True
        return True
