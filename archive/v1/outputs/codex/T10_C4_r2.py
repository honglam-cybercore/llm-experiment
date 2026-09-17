import hashlib
import hmac
import secrets
import string
import threading
import time


class CodeManager:
    _CODE_LENGTH = 8
    _EXPIRY_SECONDS = 600
    _ALPHABET = string.ascii_letters + string.digits

    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)
        self._codes = {}
        self._lock = threading.RLock()

    def generate_code(self, user_id) -> str:
        try:
            hash(user_id)
        except TypeError as exc:
            raise TypeError("user_id must be hashable") from exc

        with self._lock:
            previous = self._codes.get(user_id)
            while True:
                code = "".join(
                    secrets.choice(self._ALPHABET)
                    for _ in range(self._CODE_LENGTH)
                )
                digest = hmac.new(
                    self._secret, code.encode("ascii"), hashlib.sha256
                ).digest()
                if previous is None or not hmac.compare_digest(digest, previous[0]):
                    break

            self._codes[user_id] = (digest, time.monotonic())
            return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str) or len(code) != self._CODE_LENGTH:
            return False
        if any(character not in self._ALPHABET for character in code):
            return False

        try:
            hash(user_id)
        except TypeError:
            return False

        with self._lock:
            record = self._codes.get(user_id)
            if record is None:
                return False

            digest, created_at = record
            if time.monotonic() - created_at >= self._EXPIRY_SECONDS:
                del self._codes[user_id]
                return False

            candidate = hmac.new(
                self._secret, code.encode("ascii"), hashlib.sha256
            ).digest()
            if not hmac.compare_digest(candidate, digest):
                return False

            del self._codes[user_id]
            return True