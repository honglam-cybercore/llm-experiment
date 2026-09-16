import hashlib
import secrets
import threading
import time


class SessionManager:
    _SESSION_LIFETIME_SECONDS = 30 * 60
    _MAX_SESSION_ID_LENGTH = 256

    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.RLock()

    def create_session(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id must not be None")

        with self._lock:
            while True:
                session_id = secrets.token_urlsafe(32)
                session_key = hashlib.sha256(session_id.encode("ascii")).digest()
                if session_key not in self._sessions:
                    self._sessions[session_key] = (
                        time.monotonic() + self._SESSION_LIFETIME_SECONDS
                    )
                    return session_id

    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str):
            return False
        if not session_id or len(session_id) > self._MAX_SESSION_ID_LENGTH:
            return False

        try:
            session_key = hashlib.sha256(session_id.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            expiry = self._sessions.get(session_key)
            if expiry is None:
                return False
            if time.monotonic() >= expiry:
                del self._sessions[session_key]
                return False
            return True

    def invalidate_session(self, session_id) -> bool:
        if not isinstance(session_id, str):
            return False
        if not session_id or len(session_id) > self._MAX_SESSION_ID_LENGTH:
            return False

        try:
            session_key = hashlib.sha256(session_id.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            expiry = self._sessions.get(session_key)
            if expiry is None:
                return False
            del self._sessions[session_key]
            return time.monotonic() < expiry