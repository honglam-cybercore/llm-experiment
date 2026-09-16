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
        self._ttl = 300.0
        self._max_attempts = 5

    def generate_otp(self, user_id) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        digest = hmac.new(
            self._secret,
            otp.encode("ascii"),
            hashlib.sha256,
        ).digest()

        with self._lock:
            self._otps[user_id] = {
                "digest": digest,
                "expires_at": time.monotonic() + self._ttl,
                "attempts": 0,
                "used": False,
            }

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        if not isinstance(otp, str) or len(otp) != 6:
            return False
        if any(character < "0" or character > "9" for character in otp):
            return False

        with self._lock:
            record = self._otps.get(user_id)
            if record is None:
                return False

            if record["used"] or time.monotonic() >= record["expires_at"]:
                return False

            if record["attempts"] >= self._max_attempts:
                return False

            candidate_digest = hmac.new(
                self._secret,
                otp.encode("ascii"),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(candidate_digest, record["digest"]):
                record["attempts"] += 1
                return False

            record["used"] = True
            return True