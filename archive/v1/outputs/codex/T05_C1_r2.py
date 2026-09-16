import secrets
import threading
import time


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.Lock()
        self._timeout = 30 * 60

    def create_session(self, user_id) -> str:
        with self._lock:
            while True:
                session_id = secrets.token_urlsafe(32)
                if session_id not in self._sessions:
                    break
            self._sessions[session_id] = (user_id, time.monotonic() + self._timeout)
            return session_id

    def validate_session(self, session_id) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            _, expires_at = session
            if time.monotonic() >= expires_at:
                del self._sessions[session_id]
                return False

            return True

    def invalidate_session(self, session_id) -> bool:
        with self._lock:
            if session_id not in self._sessions:
                return False

            del self._sessions[session_id]
            return True