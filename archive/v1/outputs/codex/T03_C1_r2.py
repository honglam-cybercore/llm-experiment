import secrets
import threading
import time


class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._lock = threading.Lock()
        self._lifetime = 30 * 60

    def generate_token(self, user_id) -> str:
        with self._lock:
            token = secrets.token_urlsafe(32)
            while token in self._tokens:
                token = secrets.token_urlsafe(32)
            self._tokens[token] = (user_id, time.monotonic() + self._lifetime)
            return token

    def validate_token(self, token) -> bool:
        with self._lock:
            try:
                record = self._tokens.pop(token, None)
            except TypeError:
                return False

            if record is None:
                return False

            _, expires_at = record
            return time.monotonic() < expires_at