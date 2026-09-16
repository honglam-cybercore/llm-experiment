import hashlib
import secrets
import threading
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
        self._lock = threading.RLock()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
            raise TypeError("ttl_seconds must be an integer")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")

        with self._lock:
            while True:
                key = secrets.token_urlsafe(32)
                digest = hashlib.sha256(key.encode("utf-8")).digest()
                if digest not in self._keys:
                    break

            self._keys[digest] = {
                "owner": owner,
                "expires_at": time.monotonic() + ttl_seconds,
                "revoked": False,
            }
            return key

    def validate_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        try:
            digest = hashlib.sha256(key.encode("utf-8")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            record = self._keys.get(digest)
            if record is None:
                return False
            if record["revoked"] or time.monotonic() >= record["expires_at"]:
                return False
            return True

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        try:
            digest = hashlib.sha256(key.encode("utf-8")).digest()
        except UnicodeEncodeError:
            return False

        with self._lock:
            record = self._keys.get(digest)
            if record is None or record["revoked"]:
                return False
            record["revoked"] = True
            return True