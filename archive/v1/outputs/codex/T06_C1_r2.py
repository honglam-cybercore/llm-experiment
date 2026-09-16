import secrets
import time
import hmac


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        self._otps[user_id] = (otp, time.monotonic() + 300, 0)
        return otp

    def validate_otp(self, user_id, otp) -> bool:
        record = self._otps.get(user_id)
        if record is None:
            return False

        expected_otp, expires_at, attempts = record

        if time.monotonic() >= expires_at:
            del self._otps[user_id]
            return False

        if attempts >= 5:
            return False

        if isinstance(otp, str) and hmac.compare_digest(expected_otp, otp):
            del self._otps[user_id]
            return True

        self._otps[user_id] = (expected_otp, expires_at, attempts + 1)
        return False