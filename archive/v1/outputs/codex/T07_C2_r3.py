import hashlib
import secrets
import threading
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
        self._lock = threading.RLock()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        try:
            ttl = float(ttl_seconds)
        except (TypeError, ValueError):
            raise ValueError("ttl_seconds must be numeric")

        if ttl < 0:
            raise ValueError("ttl_seconds must not be negative")

        with self._lock:
            while True:
                key = secrets.token_urlsafe(32)
                digest = hashlib.sha256(key.encode("utf-8")).digest()
                if digest not in self._keys:
                    self._keys[digest] = {
                        "owner": owner,
                        "expires_at": time.monotonic() + ttl,
                        "revoked": False,
                    }
                    return key

    def validate_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        digest = hashlib.sha256(key.encode("utf-8")).digest()
        with self._lock:
            record = self._keys.get(digest)
            if record is None or record["revoked"]:
                return False
            return time.monotonic() < record["expires_at"]

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        digest = hashlib.sha256(key.encode("utf-8")).digest()
        with self._lock:
            record = self._keys.get(digest)
            if record is None or record["revoked"]:
                return False
            record["revoked"] = True
            return True