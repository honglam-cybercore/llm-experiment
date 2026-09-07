import uuid
import time
from typing import Dict, Tuple

class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, Tuple[str, float, bool]] = {}
        self._session_timeout = 30 * 60

    def create_session(self, user_id) -> str:
        session_id = str(uuid.uuid4())
        current_time = time.time()
        self._sessions[session_id] = (user_id, current_time, False)
        return session_id

    def validate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False

        user_id, creation_time, is_invalidated = self._sessions[session_id]

        if is_invalidated:
            return False

        current_time = time.time()
        if current_time - creation_time > self._session_timeout:
            return False

        return True

    def invalidate_session(self, session_id) -> bool:
        if session_id not in self._sessions:
            return False

        user_id, creation_time, _ = self._sessions[session_id]
        self._sessions[session_id] = (user_id, creation_time, True)
        return True
