import hashlib
import secrets
import threading
import time


class TokenManager:
    _TOKEN_LIFETIME_SECONDS = 30 * 60
    _TOKEN_BYTES = 32

    def __init__(self) -> None:
        self._tokens = {}
        self._lock = threading.Lock()

    @staticmethod
    def _digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("ascii")).digest()

    def generate_token(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id must not be None")
        if isinstance(user_id, str) and not user_id:
            raise ValueError("user_id must not be empty")

        token = secrets.token_urlsafe(self._TOKEN_BYTES)
        digest = self._digest(token)
        expires_at = time.monotonic() + self._TOKEN_LIFETIME_SECONDS

        with self._lock:
            now = time.monotonic()
            self._tokens = {
                key: expiry
                for key, expiry in self._tokens.items()
                if expiry > now
            }
            self._tokens[digest] = expires_at

        return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token or len(token) > 256:
            return False

        try:
            digest = self._digest(token)
        except (UnicodeEncodeError, ValueError):
            return False

        with self._lock:
            expires_at = self._tokens.get(digest)
            if expires_at is None:
                return False

            if time.monotonic() >= expires_at:
                del self._tokens[digest]
                return False

            del self._tokens[digest]
            return True