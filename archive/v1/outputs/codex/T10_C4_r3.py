import secrets
import string
import threading
import time


class CodeManager:
    _CODE_LENGTH = 8
    _EXPIRY_SECONDS = 600
    _ALPHABET = string.ascii_letters + string.digits

    def __init__(self) -> None:
        self._codes = {}
        self._lock = threading.RLock()

    def generate_code(self, user_id) -> str:
        try:
            hash(user_id)
        except (TypeError, ValueError):
            raise TypeError("user_id must be hashable")

        with self._lock:
            previous = self._codes.get(user_id)
            previous_code = previous[0] if previous else None

            code = self._new_code()
            while code == previous_code:
                code = self._new_code()

            self._codes[user_id] = (
                code,
                time.monotonic() + self._EXPIRY_SECONDS,
            )
            return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str):
            return False
        if len(code) != self._CODE_LENGTH or not code.isascii() or not code.isalnum():
            return False

        try:
            hash(user_id)
        except (TypeError, ValueError):
            return False

        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            expected_code, expires_at = record
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            if not secrets.compare_digest(expected_code, code):
                return False

            del self._codes[user_id]
            return True

    @classmethod
    def _new_code(cls) -> str:
        return "".join(secrets.choice(cls._ALPHABET) for _ in range(cls._CODE_LENGTH))