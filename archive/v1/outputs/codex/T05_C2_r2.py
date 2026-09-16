import secrets
import threading
import time


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.Lock()
        self._expiry_seconds = 30 * 60

    def create_session(self, user_id) -> str:
        with self._lock:
            session_id = secrets.token_urlsafe(32)
            while session_id in self._sessions:
                session_id = secrets.token_urlsafe(32)
            self._sessions[session_id] = (user_id, time.monotonic() + self._expiry_seconds)
            return session_id

    def validate_session(self, session_id) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            if time.monotonic() >= session[1]:
                del self._sessions[session_id]
                return False
            return True

    def invalidate_session(self, session_id) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            if time.monotonic() >= session[1]:
                del self._sessions[session_id]
                return False
            del self._sessions[session_id]
            return True