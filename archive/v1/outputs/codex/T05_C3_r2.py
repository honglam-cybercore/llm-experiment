import hashlib
import secrets
import threading
import time


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.RLock()
        self._lifetime = 30 * 60

    def create_session(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id is required")

        with self._lock:
            self._remove_expired()
            while True:
                session_id = secrets.token_urlsafe(32)
                session_key = hashlib.sha256(session_id.encode("ascii")).digest()
                if session_key not in self._sessions:
                    self._sessions[session_key] = (
                        time.monotonic() + self._lifetime,
                        False,
                    )
                    return session_id

    def validate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id or len(session_id) > 256:
            return False

        try:
            session_key = hashlib.sha256(session_id.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            record = self._sessions.get(session_key)
            if record is None:
                return False

            expires_at, invalidated = record
            if invalidated or time.monotonic() >= expires_at:
                self._sessions.pop(session_key, None)
                return False

            return True

    def invalidate_session(self, session_id) -> bool:
        if not isinstance(session_id, str) or not session_id or len(session_id) > 256:
            return False

        try:
            session_key = hashlib.sha256(session_id.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            record = self._sessions.get(session_key)
            if record is None:
                return False

            expires_at, invalidated = record
            if invalidated or time.monotonic() >= expires_at:
                self._sessions.pop(session_key, None)
                return False

            self._sessions[session_key] = (expires_at, True)
            return True

    def _remove_expired(self) -> None:
        now = time.monotonic()
        expired = [
            key
            for key, (expires_at, _) in self._sessions.items()
            if expires_at <= now
        ]
        for key in expired:
            self._sessions.pop(key, None)