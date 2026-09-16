import hashlib
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

    @staticmethod
    def _validate_key_input(key) -> bool:
        return isinstance(key, str) and 1 <= len(key) <= 4096

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
            raise TypeError("ttl_seconds must be an integer")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")

        expires_at = time.monotonic() + ttl_seconds

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
        if not self._validate_key_input(key):
            return False

        record = self._keys.get(self._digest(key))
        if record is None:
            return False

        with self._lock:
            record = self._keys.get(self._digest(key))
            if record is None or record["revoked"]:
                return False
            if time.monotonic() >= record["expires_at"]:
                record["revoked"] = True
                return False
            return True

    def revoke_key(self, key) -> bool:
        if not self._validate_key_input(key):
            return False

        with self._lock:
            record = self._keys.get(self._digest(key))
            if record is None or record["revoked"]:
                return False
            record["revoked"] = True
            return True