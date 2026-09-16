import hashlib
import hmac
import secrets
import threading
import time


class OTPManager:
    def __init__(self) -> None:
        self._records = {}
        self._secret = secrets.token_bytes(32)
        self._lock = threading.RLock()
        self._lifetime = 300.0
        self._max_attempts = 5

    def generate_otp(self, user_id) -> str:
        key = self._normalize_user_id(user_id)
        otp = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_bytes(16)
        digest = self._digest(salt, otp)

        with self._lock:
            self._remove_expired()
            self._records[key] = (salt, digest, time.monotonic() + self._lifetime, 0)

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        try:
            key = self._normalize_user_id(user_id)
            if not isinstance(otp, str) or len(otp) != 6 or not otp.isascii() or not otp.isdigit():
                return False
        except (TypeError, ValueError):
            return False

        with self._lock:
            record = self._records.get(key)
            if record is None:
                return False

            salt, expected_digest, expires_at, attempts = record
            if time.monotonic() >= expires_at or attempts >= self._max_attempts:
                self._records.pop(key, None)
                return False

            actual_digest = self._digest(salt, otp)
            if not hmac.compare_digest(actual_digest, expected_digest):
                attempts += 1
                if attempts >= self._max_attempts:
                    self._records.pop(key, None)
                else:
                    self._records[key] = (salt, expected_digest, expires_at, attempts)
                return False

            self._records.pop(key, None)
            return True

    def _digest(self, salt: bytes, otp: str) -> bytes:
        return hmac.new(
            self._secret,
            salt + otp.encode("ascii"),
            hashlib.sha256,
        ).digest()

    @staticmethod
    def _normalize_user_id(user_id):
        if not isinstance(user_id, str):
            raise TypeError("user_id must be a string")
        if not user_id or len(user_id) > 256:
            raise ValueError("invalid user_id")
        return user_id

    def _remove_expired(self) -> None:
        now = time.monotonic()
        expired = [
            key for key, record in self._records.items()
            if now >= record[2]
        ]
        for key in expired:
            self._records.pop(key, None)