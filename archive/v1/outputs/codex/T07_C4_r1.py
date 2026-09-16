import hashlib
import hmac
import math
import secrets
import threading
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
        self._lock = threading.RLock()

    @staticmethod
    def _digest(key: str) -> bytes:
        return hashlib.sha256(key.encode("utf-8")).digest()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float)):
            raise TypeError("ttl_seconds must be a finite non-negative number")
        if not math.isfinite(float(ttl_seconds)) or ttl_seconds < 0:
            raise ValueError("ttl_seconds must be a finite non-negative number")

        expires_at = time.monotonic() + float(ttl_seconds)

        with self._lock:
            while True:
                key = secrets.token_urlsafe(32)
                digest = self._digest(key)
                if digest not in self._keys:
                    self._keys[digest] = {
                        "owner": owner,
                        "expires_at": expires_at,
                        "revoked": False,
                    }
                    return key

    def validate_key(self, key) -> bool:
        if not isinstance(key, str) or not key or len(key) > 512:
            return False

        digest = self._digest(key)
        with self._lock:
            record = self._keys.get(digest)
            if record is None:
                return False

            return (
                hmac.compare_digest(digest, self._digest(key))
                and not record["revoked"]
                and time.monotonic() < record["expires_at"]
            )

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str) or not key or len(key) > 512:
            return False

        digest = self._digest(key)
        with self._lock:
            record = self._keys.get(digest)
            if record is None or record["revoked"]:
                return False

            record["revoked"] = True
            return True