import hashlib
import hmac
import secrets
import threading
import time


class OTPManager:
    def __init__(self) -> None:
        self._key = secrets.token_bytes(32)
        self._otps = {}
        self._lock = threading.RLock()

    def generate_otp(self, user_id) -> str:
        if not isinstance(user_id, str) or not user_id or len(user_id) > 256:
            raise ValueError("invalid user_id")

        otp = f"{secrets.randbelow(1_000_000):06d}"
        message = user_id.encode("utf-8") + b"\x00" + otp.encode("ascii")
        digest = hmac.new(self._key, message, hashlib.sha256).digest()

        with self._lock:
            self._otps[user_id] = (digest, time.monotonic() + 300.0, 0, False)

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        if (
            not isinstance(user_id, str)
            or not user_id
            or len(user_id) > 256
            or not isinstance(otp, str)
            or len(otp) != 6
            or not otp.isascii()
            or not otp.isdecimal()
        ):
            return False

        message = user_id.encode("utf-8") + b"\x00" + otp.encode("ascii")
        candidate = hmac.new(self._key, message, hashlib.sha256).digest()

        with self._lock:
            record = self._otps.get(user_id)
            if record is None:
                return False

            expected, expires_at, attempts, used = record

            if used or time.monotonic() >= expires_at:
                self._otps.pop(user_id, None)
                return False

            if hmac.compare_digest(candidate, expected):
                self._otps.pop(user_id, None)
                return True

            attempts += 1
            if attempts >= 5:
                self._otps.pop(user_id, None)
            else:
                self._otps[user_id] = (expected, expires_at, attempts, used)

            return False