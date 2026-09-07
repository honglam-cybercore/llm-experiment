import uuid
import time
from typing import Dict

class SessionManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = 30 * 60

    def create_session(self, user_id) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': time.time(),
            'invalidated': False
        }
        return session_id

    def validate_session(self, session_id) -> bool:
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        if session['invalidated']:
            return False

        if time.time() - session['created_at'] > self.session_timeout:
            return False

        return True

    def invalidate_session(self, session_id) -> bool:
        if session_id not in self.sessions:
            return False

        self.sessions[session_id]['invalidated'] = True
        return True
