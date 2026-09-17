import secrets
import string
import threading
import time


class CodeManager:
    _ALPHABET = string.ascii_letters + string.digits
    _EXPIRY_SECONDS = 600

    def __init__(self) -> None:
        self._codes = {}
        self._lock = threading.Lock()

    def generate_code(self, user_id) -> str:
        with self._lock:
            previous = self._codes.get(user_id)
            code = secrets.choice(self._ALPHABET)
            while previous is not None and code == previous[0]:
                code = "".join(secrets.choice(self._ALPHABET) for _ in range(8))

            if len(code) == 1:
                code += "".join(secrets.choice(self._ALPHABET) for _ in range(7))

            self._codes[user_id] = (code, time.monotonic() + self._EXPIRY_SECONDS, False)
            return code

    def validate_code(self, user_id, code) -> bool:
        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            expected, expires_at, used = record
            if used or time.monotonic() >= expires_at:
                return False

            if not isinstance(code, str) or len(code) != 8:
                return False

            if not secrets.compare_digest(expected, code):
                return False

            self._codes[user_id] = (expected, expires_at, True)
            return True