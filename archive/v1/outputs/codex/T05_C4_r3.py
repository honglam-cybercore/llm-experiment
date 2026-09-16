import secrets
import threading
import time


class SessionManager:
    SESSION_DURATION_SECONDS = 30 * 60
    SESSION_ID_BYTES = 32

    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.RLock()

    def create_session(self, user_id) -> str:
        del user_id

        with self._lock:
            while True:
                session_id = secrets.token_urlsafe(self.SESSION_ID_BYTES)
                if session_id not in self._sessions:
                    self._sessions[session_id] = (
                        time.monotonic() + self.SESSION_DURATION_SECONDS
                    )
                    return session_id

    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False

        with self._lock:
            expires_at = self._sessions.get(session_id)
            if expires_at is None:
                return False

            if time.monotonic() >= expires_at:
                del self._sessions[session_id]
                return False

            return True

    def invalidate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False

        with self._lock:
            expires_at = self._sessions.get(session_id)
            if expires_at is None:
                return False

            if time.monotonic() >= expires_at:
                del self._sessions[session_id]
                return False

            del self._sessions[session_id]
            return True