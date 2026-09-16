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
                    self._tokens[token] = time.monotonic() + self._lifetime
                    return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str):
            return False

        now = time.monotonic()
        with self._lock:
            expiry = self._tokens.get(token)
            if expiry is None:
                return False

            del self._tokens[token]
            return now < expiry