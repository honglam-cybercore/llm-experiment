import hashlib
import hmac
import secrets
import threading
import time


class OTPManager:
    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)
        self._otps = {}
        self._lock = threading.RLock()

    def generate_otp(self, user_id) -> str:
        try:
            hash(user_id)
        except (TypeError, ValueError):
            raise TypeError("user_id must be hashable")

        otp = f"{secrets.randbelow(1_000_000):06d}"
        digest = hmac.new(
            self._secret,
            str(user_id).encode("utf-8") + b"\x00" + otp.encode("ascii"),
            hashlib.sha256,
        ).digest()

        with self._lock:
            self._otps[user_id] = {
                "digest": digest,
                "expires_at": time.monotonic() + 300.0,
                "attempts": 0,
                "used": False,
            }

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        try:
            hash(user_id)
        except (TypeError, ValueError):
            return False

        with self._lock:
            record = self._otps.get(user_id)
            if record is None or record["used"] or record["attempts"] >= 5:
                return False

            if time.monotonic() >= record["expires_at"]:
                record["used"] = True
                return False

            if not isinstance(otp, str) or len(otp) != 6 or not otp.isascii() or not otp.isdigit():
                record["attempts"] += 1
                return False

            digest = hmac.new(
                self._secret,
                str(user_id).encode("utf-8") + b"\x00" + otp.encode("ascii"),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(record["digest"], digest):
                record["attempts"] += 1
                return False

            record["used"] = True
            return True