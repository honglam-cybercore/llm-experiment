import hashlib
import hmac
import secrets
import string
import threading
import time


class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._lock = threading.RLock()
        self._alphabet = string.ascii_letters + string.digits

    def generate_code(self, user_id) -> str:
        with self._lock:
            previous = self._codes.get(user_id)
            previous_digest = previous[0] if previous else None

            while True:
                code = "".join(secrets.choice(self._alphabet) for _ in range(8))
                digest = hashlib.sha256(code.encode("ascii")).digest()
                if previous_digest is None or not hmac.compare_digest(
                    digest, previous_digest
                ):
                    break

            self._codes[user_id] = (digest, time.monotonic() + 600)
            return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str) or len(code) != 8:
            return False

        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            digest, expires_at = record
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            candidate_digest = hashlib.sha256(code.encode("ascii")).digest()
            if not hmac.compare_digest(digest, candidate_digest):
                return False

            del self._codes[user_id]
            return True