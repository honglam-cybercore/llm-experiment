import hashlib
import hmac
import secrets
import string
import threading
import time


class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._lock = threading.Lock()
        self._secret = secrets.token_bytes(32)
        self._alphabet = string.ascii_letters + string.digits
        self._expiry_seconds = 600

    def generate_code(self, user_id) -> str:
        code = "".join(secrets.choice(self._alphabet) for _ in range(8))
        digest = hmac.new(
            self._secret,
            f"{user_id!r}:{code}".encode(),
            hashlib.sha256,
        ).digest()
        with self._lock:
            self._codes[user_id] = (digest, time.monotonic() + self._expiry_seconds)
        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str):
            return False

        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            digest, expires_at = record
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            candidate = hmac.new(
                self._secret,
                f"{user_id!r}:{code}".encode(),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(digest, candidate):
                return False

            del self._codes[user_id]
            return True