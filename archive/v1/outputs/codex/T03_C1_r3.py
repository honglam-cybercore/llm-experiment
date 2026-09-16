import secrets
import threading
import time


class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._lock = threading.Lock()
        self._lifetime = 30 * 60

    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = time.monotonic() + self._lifetime

        with self._lock:
            self._tokens[token] = (user_id, expires_at)

        return token

    def validate_token(self, token) -> bool:
        with self._lock:
            record = self._tokens.pop(token, None)

        if record is None:
            return False

        _, expires_at = record
        return time.monotonic() < expires_at