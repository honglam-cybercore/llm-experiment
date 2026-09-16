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
            now = time.monotonic()
            self._tokens = {
                token: entry
                for token, entry in self._tokens.items()
                if entry[0] > now
            }

            while True:
                token = secrets.token_urlsafe(32)
                if token not in self._tokens:
                    self._tokens[token] = (now + self._lifetime, user_id)
                    return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str):
            return False

        with self._lock:
            entry = self._tokens.pop(token, None)
            if entry is None:
                return False
            return time.monotonic() < entry[0]