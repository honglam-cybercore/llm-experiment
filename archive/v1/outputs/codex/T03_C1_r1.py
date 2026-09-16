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
            while True:
                token = secrets.token_urlsafe(32)
                if token not in self._tokens:
                    self._tokens[token] = (user_id, time.monotonic() + self._lifetime)
                    return token

    def validate_token(self, token) -> bool:
        try:
            with self._lock:
                entry = self._tokens.get(token)
                if entry is None:
                    return False

                _, expires_at = entry
                del self._tokens[token]

                return time.monotonic() < expires_at
        except (TypeError, AttributeError):
            return False