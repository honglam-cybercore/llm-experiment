import hashlib
import hmac
import secrets
import string
import threading
import time


class CodeManager:
    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)
        self._codes = {}
        self._lock = threading.RLock()
        self._alphabet = string.ascii_letters + string.digits
        self._ttl = 600.0

    def _digest(self, code: str) -> bytes:
        return hmac.digest(self._secret, code.encode("ascii"), hashlib.sha256)

    def generate_code(self, user_id) -> str:
        try:
            hash(user_id)
        except (TypeError, ValueError):
            raise TypeError("user_id must be hashable")

        code = "".join(secrets.choice(self._alphabet) for _ in range(8))
        record = (self._digest(code), time.monotonic() + self._ttl)

        with self._lock:
            self._codes[user_id] = record

        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str) or len(code) != 8 or not code.isascii() or not code.isalnum():
            return False

        try:
            hash(user_id)
        except (TypeError, ValueError):
            return False

        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            expected_digest, expires_at = record
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            if not hmac.compare_digest(expected_digest, self._digest(code)):
                return False

            del self._codes[user_id]
            return True