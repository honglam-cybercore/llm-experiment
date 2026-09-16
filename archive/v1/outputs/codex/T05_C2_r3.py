import time
import uuid


class SessionManager:
    def __init__(self) -> None:
        self._sessions = {}

    def create_session(self, user_id) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "user_id": user_id,
            "expires_at": time.monotonic() + 30 * 60,
            "invalidated": False,
        }
        return session_id

    def validate_session(self, session_id) -> bool:
        session = self._sessions.get(session_id)
        if session is None or session["invalidated"]:
            return False
        if time.monotonic() >= session["expires_at"]:
            return False
        return True

    def invalidate_session(self, session_id) -> bool:
        session = self._sessions.get(session_id)
        if session is None or session["invalidated"]:
            return False
        session["invalidated"] = True
        return True