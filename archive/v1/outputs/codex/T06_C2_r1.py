import secrets
import time


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        self._otps[user_id] = {
            "otp": otp,
            "expires_at": time.time() + 300,
            "attempts": 0,
        }
        return otp

    def validate_otp(self, user_id, otp) -> bool:
        record = self._otps.get(user_id)

        if record is None:
            return False

        if time.time() >= record["expires_at"]:
            del self._otps[user_id]
            return False

        if record["attempts"] >= 5:
            return False

        if (
            not isinstance(otp, str)
            or len(otp) != 6
            or not otp.isascii()
            or not otp.isdigit()
            or otp != record["otp"]
        ):
            record["attempts"] += 1
            return False

        del self._otps[user_id]
        return True