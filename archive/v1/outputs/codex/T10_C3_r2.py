import hashlib
import hmac
import secrets
import string
import threading
import time


class CodeManager:
    def __init__(self) -> None:
        self._key = secrets.token_bytes(32)
        self._codes = {}
        self._lock = threading.RLock()
        self._alphabet = string.ascii_letters + string.digits
        self._lifetime = 600.0

    def generate_code(self, user_id) -> str:
        try:
            hash(user_id)
        except Exception:
            raise ValueError("user_id must be hashable") from None

        code = "".join(secrets.choice(self._alphabet) for _ in range(8))
        digest = hmac.new(
            self._key,
            code.encode("ascii"),
            hashlib.sha256,
        ).digest()
        expires_at = time.monotonic() + self._lifetime

        with self._lock:
            self._codes[user_id] = (digest, expires_at)

        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str) or len(code) != 8 or not code.isascii():
            return False
        if any(character not in self._alphabet for character in code):
            return False

        try:
            hash(user_id)
        except Exception:
            return False

        digest = hmac.new(
            self._key,
            code.encode("ascii"),
            hashlib.sha256,
        ).digest()

        with self._lock:
            stored = self._codes.get(user_id)
            if stored is None:
                return False

            expected_digest, expires_at = stored
            if time.monotonic() >= expires_at:
                self._codes.pop(user_id, None)
                return False

            if not hmac.compare_digest(digest, expected_digest):
                return False

            self._codes.pop(user_id, None)
            return True