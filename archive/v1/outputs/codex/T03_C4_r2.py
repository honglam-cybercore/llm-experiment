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
        expires_at = time.monotonic() + self._lifetime

        with self._lock:
            now = time.monotonic()
            expired = [
                stored_hash
                for stored_hash, expiry in self._tokens.items()
                if expiry <= now
            ]
            for stored_hash in expired:
                del self._tokens[stored_hash]

            while token_hash in self._tokens:
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode("ascii")).digest()

            self._tokens[token_hash] = expires_at

        return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token or len(token) > 512:
            return False

        try:
            token_hash = hashlib.sha256(token.encode("ascii")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            expires_at = self._tokens.get(token_hash)
            if expires_at is None:
                return False

            if expires_at <= time.monotonic():
                del self._tokens[token_hash]
                return False

            del self._tokens[token_hash]
            return True