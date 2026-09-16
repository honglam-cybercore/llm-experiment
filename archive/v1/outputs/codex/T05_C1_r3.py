import secrets
import threading
import time


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._issued_ids = set()
        self._lock = threading.Lock()
        self._timeout = 30 * 60

    def create_session(self, user_id) -> str:
        with self._lock:
            session_id = secrets.token_urlsafe(32)
            while session_id in self._issued_ids:
                session_id = secrets.token_urlsafe(32)

            self._issued_ids.add(session_id)
            self._sessions[session_id] = (user_id, time.monotonic() + self._timeout)
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
            return self._sessions.pop(session_id, None) is not None