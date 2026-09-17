import secrets
import string
import threading
import time


class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._lock = threading.Lock()
        self._alphabet = string.ascii_letters + string.digits
        self._expiration_seconds = 600

    def generate_code(self, user_id) -> str:
        code = "".join(secrets.choice(self._alphabet) for _ in range(8))
        expires_at = time.monotonic() + self._expiration_seconds

        with self._lock:
            self._codes[user_id] = (code, expires_at, False)

        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str):
            return False

        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            expected_code, expires_at, used = record

            if used or time.monotonic() >= expires_at:
                self._codes.pop(user_id, None)
                return False

            if not secrets.compare_digest(expected_code, code):
                return False

            self._codes[user_id] = (expected_code, expires_at, True)
            return True