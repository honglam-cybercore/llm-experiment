import hashlib
import hmac
import secrets
import threading
import time


class TokenManager:
    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)
        self._tokens: dict[bytes, float] = {}
        self._lock = threading.Lock()
        self._token_ttl = 30 * 60

    def generate_token(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id must not be None")

        with self._lock:
            self._remove_expired()
            while True:
                token = secrets.token_urlsafe(32)
                token_key = hmac.new(
                    self._secret,
                    token.encode("ascii"),
                    hashlib.sha256,
                ).digest()
                if token_key not in self._tokens:
                    self._tokens[token_key] = time.monotonic() + self._token_ttl
                    return token

    def validate_token(self, token) -> bool:
        if type(token) is not str or not token or len(token) > 512:
            return False

        try:
            token_bytes = token.encode("ascii")
        except UnicodeEncodeError:
            return False

        token_key = hmac.new(
            self._secret,
            token_bytes,
            hashlib.sha256,
        ).digest()

        with self._lock:
            expires_at = self._tokens.get(token_key)
            if expires_at is None:
                return False

            if time.monotonic() >= expires_at:
                del self._tokens[token_key]
                return False

            del self._tokens[token_key]
            return True

    def _remove_expired(self) -> None:
        now = time.monotonic()
        expired = [
            token_key
            for token_key, expires_at in self._tokens.items()
            if now >= expires_at
        ]
        for token_key in expired:
            del self._tokens[token_key]