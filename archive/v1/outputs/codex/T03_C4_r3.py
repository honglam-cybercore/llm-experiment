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

        with self._lock:
            now = time.monotonic()
            self._remove_expired(now)

            while True:
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode("ascii")).digest()
                if token_hash not in self._tokens:
                    self._tokens[token_hash] = now + self._lifetime
                    return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token.isascii():
            return False

        try:
            token_hash = hashlib.sha256(token.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            expiry = self._tokens.pop(token_hash, None)
            if expiry is None:
                return False

            if time.monotonic() >= expiry:
                return False

            return True

    def _remove_expired(self, now: float) -> None:
        expired = [
            token_hash
            for token_hash, expiry in self._tokens.items()
            if now >= expiry
        ]
        for token_hash in expired:
            del self._tokens[token_hash]