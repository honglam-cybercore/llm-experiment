import secrets
import time


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        self._otps[user_id] = [otp, time.monotonic() + 300, 0, False]
        return otp

    def validate_otp(self, user_id, otp) -> bool:
        record = self._otps.get(user_id)
        if record is None:
            return False

        expected, expires_at, attempts, used = record

        if used or time.monotonic() >= expires_at or attempts >= 5:
            return False

        if not isinstance(otp, str) or len(otp) != 6 or not otp.isascii() or not otp.isdigit():
            record[2] += 1
            return False

        if not secrets.compare_digest(expected, otp):
            record[2] += 1
            return False

        record[3] = True
        return True