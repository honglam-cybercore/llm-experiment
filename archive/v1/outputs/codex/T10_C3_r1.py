import hashlib
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
            raise ValueError("user_id must be hashable")

        code = "".join(
            secrets.choice(self._ALPHABET) for _ in range(self._CODE_LENGTH)
        )
        code_digest = hashlib.sha256(code.encode("ascii")).digest()
        expires_at = time.monotonic() + self._EXPIRY_SECONDS

        with self._lock:
            self._codes[user_id] = (code_digest, expires_at)

        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str) or len(code) != self._CODE_LENGTH:
            return False
        if any(character not in self._ALPHABET for character in code):
            return False

        try:
            hash(user_id)
        except (TypeError, ValueError):
            return False

        with self._lock:
            stored = self._codes.get(user_id)
            if stored is None:
                return False

            stored_digest, expires_at = stored
            if time.monotonic() >= expires_at:
                del self._codes[user_id]
                return False

            supplied_digest = hashlib.sha256(code.encode("ascii")).digest()
            if not secrets.compare_digest(stored_digest, supplied_digest):
                return False

            del self._codes[user_id]
            return True