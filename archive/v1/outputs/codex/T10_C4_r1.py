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
        self._lock = threading.Lock()
        self._ttl = 10 * 60
        self._alphabet = string.ascii_letters + string.digits

    def _digest(self, code: str) -> bytes:
        return hmac.new(
            self._secret,
            code.encode("ascii"),
            hashlib.sha256,
        ).digest()

    def generate_code(self, user_id) -> str:
        try:
            hash(user_id)
        except (TypeError, ValueError):
            raise TypeError("user_id must be hashable") from None

        code = "".join(secrets.choice(self._alphabet) for _ in range(8))
        entry = (self._digest(code), time.monotonic() + self._ttl)

        with self._lock:
            self._codes[user_id] = entry

        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str) or len(code) != 8:
            return False
        if any(character not in self._alphabet for character in code):
            return False

        try:
            hash(user_id)
        except (TypeError, ValueError):
            return False

        with self._lock:
            entry = self._codes.get(user_id)
            if entry is None:
                return False

            expected_digest, expires_at = entry
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            valid = hmac.compare_digest(self._digest(code), expected_digest)
            if valid:
                del self._codes[user_id]

            return valid