import secrets
import time
import threading


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._lock = threading.RLock()
        self._expiry_seconds = 300
        self._max_attempts = 5

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        with self._lock:
            self._otps[user_id] = {
                "otp": otp,
                "expires_at": time.monotonic() + self._expiry_seconds,
                "attempts": 0,
            }
        return otp

    def validate_otp(self, user_id, otp) -> bool:
        with self._lock:
            record = self._otps.get(user_id)
            if record is None:
                return False

            if time.monotonic() >= record["expires_at"]:
                del self._otps[user_id]
                return False

            if record["attempts"] >= self._max_attempts:
                return False

            if not isinstance(otp, str) or not secrets.compare_digest(record["otp"], otp):
                record["attempts"] += 1
                return False

            del self._otps[user_id]
            return True