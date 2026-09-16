import secrets
import time
from threading import Lock


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._lock = Lock()
        self._expiry_seconds = 300
        self._max_incorrect_attempts = 5

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = time.monotonic() + self._expiry_seconds

        with self._lock:
            self._otps[user_id] = [otp, expires_at, 0]

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        with self._lock:
            record = self._otps.get(user_id)

            if record is None:
                return False

            if time.monotonic() >= record[1]:
                del self._otps[user_id]
                return False

            if record[2] >= self._max_incorrect_attempts:
                return False

            if isinstance(otp, str) and secrets.compare_digest(record[0], otp):
                del self._otps[user_id]
                return True

            record[2] += 1
            return False