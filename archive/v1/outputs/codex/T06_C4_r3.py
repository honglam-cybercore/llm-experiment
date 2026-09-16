import hashlib
import hmac
import secrets
import threading
import time


class OTPManager:
    def __init__(self) -> None:
        self._records = {}
        self._lock = threading.RLock()
        self._lifetime = 300.0
        self._max_attempts = 5

    def generate_otp(self, user_id) -> str:
        hash(user_id)

        otp = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_bytes(16)
        digest = hashlib.sha256(salt + otp.encode("ascii")).digest()

        with self._lock:
            self._records[user_id] = {
                "salt": salt,
                "digest": digest,
                "expires_at": time.monotonic() + self._lifetime,
                "attempts": 0,
            }

        return otp

    def validate_otp(self, user_id, otp) -> bool:
        hash(user_id)

        if not isinstance(otp, str) or len(otp) != 6:
            formatted_otp = None
        elif all("0" <= character <= "9" for character in otp):
            formatted_otp = otp
        else:
            formatted_otp = None

        with self._lock:
            record = self._records.get(user_id)

            if record is None:
                return False

            if time.monotonic() >= record["expires_at"]:
                del self._records[user_id]
                return False

            if record["attempts"] >= self._max_attempts:
                del self._records[user_id]
                return False

            if formatted_otp is None:
                record["attempts"] += 1
                if record["attempts"] >= self._max_attempts:
                    del self._records[user_id]
                return False

            candidate_digest = hashlib.sha256(
                record["salt"] + formatted_otp.encode("ascii")
            ).digest()

            if not hmac.compare_digest(candidate_digest, record["digest"]):
                record["attempts"] += 1
                if record["attempts"] >= self._max_attempts:
                    del self._records[user_id]
                return False

            del self._records[user_id]
            return True