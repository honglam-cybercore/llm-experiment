import secrets
import string
import time
import hmac
import threading


class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._lock = threading.Lock()
        self._lifetime = 600

    def generate_code(self, user_id) -> str:
        code = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        with self._lock:
            self._codes[user_id] = (code, time.monotonic() + self._lifetime)
        return code

    def validate_code(self, user_id, code) -> bool:
        with self._lock:
            entry = self._codes.get(user_id)
            if entry is None:
                return False

            stored_code, expires_at = entry
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            if not isinstance(code, str) or not hmac.compare_digest(stored_code, code):
                return False

            del self._codes[user_id]
            return True