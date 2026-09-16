import secrets
import threading
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
        self._lock = threading.RLock()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        ttl = float(ttl_seconds)
        expires_at = time.monotonic() + ttl

        with self._lock:
            while True:
                key = secrets.token_urlsafe(32)
                if key not in self._keys:
                    self._keys[key] = {
                        "owner": owner,
                        "expires_at": expires_at,
                        "revoked": False,
                    }
                    return key

    def validate_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        with self._lock:
            record = self._keys.get(key)
            if record is None:
                return False
            return (
                not record["revoked"]
                and time.monotonic() < record["expires_at"]
            )

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        with self._lock:
            record = self._keys.get(key)
            if record is None or record["revoked"]:
                return False
            record["revoked"] = True
            return True