import hashlib
import hmac
import secrets
import threading
import time


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._lock = threading.Lock()
        self._expiration_seconds = 300
        self._max_attempts = 5

    def generate_otp(self, user_id) -> str:
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("user_id must be a non-empty string")

        otp = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_bytes(16)
        digest = hashlib.sha256(salt + otp.encode("ascii")).digest()

        with self._lock:
            self._otps[user_id] = (salt, digest, time.monotonic() + self._expiration_seconds, 0)

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        if not isinstance(user_id, str) or not user_id:
            return False
        if (
            not isinstance(otp, str)
            or len(otp) != 6
            or any(character < "0" or character > "9" for character in otp)
        ):
            return False

        with self._lock:
            record = self._otps.get(user_id)
            if record is None:
                return False

            salt, expected_digest, expires_at, attempts = record

            if time.monotonic() >= expires_at:
                del self._otps[user_id]
                return False

            supplied_digest = hashlib.sha256(salt + otp.encode("ascii")).digest()

            if hmac.compare_digest(supplied_digest, expected_digest):
                del self._otps[user_id]
                return True

            attempts += 1
            if attempts >= self._max_attempts:
                del self._otps[user_id]
            else:
                self._otps[user_id] = (salt, expected_digest, expires_at, attempts)

            return False