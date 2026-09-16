import hashlib
import secrets
import threading
import time


class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._lock = threading.Lock()
        self._lifetime = 30 * 60

    def generate_token(self, user_id) -> str:
        del user_id
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("ascii")).digest()
        expiry = time.monotonic() + self._lifetime

        with self._lock:
            now = time.monotonic()
            self._tokens = {
                key: value for key, value in self._tokens.items()
                if value > now
            }
            self._tokens[token_hash] = expiry

        return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token or len(token) > 512:
            return False

        try:
            token_hash = hashlib.sha256(token.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            expiry = self._tokens.pop(token_hash, None)
            if expiry is None:
                return False
            return time.monotonic() < expiry
