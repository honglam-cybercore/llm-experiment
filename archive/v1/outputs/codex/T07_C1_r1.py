import secrets
import threading
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
        self._lock = threading.RLock()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        key = secrets.token_urlsafe(32)
        expires_at = time.time() + max(0, float(ttl_seconds))

        with self._lock:
            while key in self._keys:
                key = secrets.token_urlsafe(32)
            self._keys[key] = {
                "owner": owner,
                "expires_at": expires_at,
                "revoked": False,
            }

        return key

    def validate_key(self, key) -> bool:
        with self._lock:
            record = self._keys.get(key)
            return bool(
                record
                and not record["revoked"]
                and time.time() < record["expires_at"]
            )

    def revoke_key(self, key) -> bool:
        with self._lock:
            record = self._keys.get(key)
            if record is None or record["revoked"]:
                return False
            record["revoked"] = True
            return True