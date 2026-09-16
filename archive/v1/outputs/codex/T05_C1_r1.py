import secrets
import threading
import time


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}
        self._lock = threading.Lock()
        self._lifetime = 30 * 60

    def create_session(self, user_id) -> str:
        with self._lock:
            while True:
                session_id = secrets.token_urlsafe(32)
                if session_id not in self._sessions:
                    break

            self._sessions[session_id] = {
                "user_id": user_id,
                "expires_at": time.monotonic() + self._lifetime,
                "invalidated": False,
            }
            return session_id

    def validate_session(self, session_id) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session["invalidated"]:
                return False

            if time.monotonic() >= session["expires_at"]:
                session["invalidated"] = True
                return False

            return True

    def invalidate_session(self, session_id) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session["invalidated"]:
                return False

            session["invalidated"] = True
            return True