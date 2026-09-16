import secrets
import threading
import time


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.RLock()
        self._ttl = 30 * 60

    def create_session(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id must not be None")

        with self._lock:
            now = time.monotonic()
            self._sessions = {
                session_id: expiry
                for session_id, expiry in self._sessions.items()
                if expiry > now
            }

            while True:
                session_id = secrets.token_urlsafe(32)
                if session_id not in self._sessions:
                    self._sessions[session_id] = now + self._ttl
                    return session_id

    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False

        with self._lock:
            expiry = self._sessions.get(session_id)
            if expiry is None:
                return False
            if time.monotonic() >= expiry:
                del self._sessions[session_id]
                return False
            return True

    def invalidate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id:
            return False

        with self._lock:
            expiry = self._sessions.pop(session_id, None)
            return expiry is not None and time.monotonic() < expiry