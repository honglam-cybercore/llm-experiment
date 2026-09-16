import secrets
import time
import hmac


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        self._otps[user_id] = {
            "otp": otp,
            "expires_at": time.monotonic() + 300,
            "attempts": 0,
            "used": False,
        }
        return otp

    def validate_otp(self, user_id, otp) -> bool:
        record = self._otps.get(user_id)

        if record is None or record["used"]:
            return False

        if time.monotonic() >= record["expires_at"]:
            return False

        if record["attempts"] >= 5:
            return False

        if not isinstance(otp, str) or len(otp) != 6 or not otp.isdigit():
            record["attempts"] += 1
            return False

        if not hmac.compare_digest(record["otp"], otp):
            record["attempts"] += 1
            return False

        record["used"] = True
        return True