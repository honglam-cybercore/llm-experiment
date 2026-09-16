import secrets
import threading
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
        self._lock = threading.Lock()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")

        with self._lock:
            while True:
                key = secrets.token_urlsafe(32)
                if key not in self._keys:
                    break

            self._keys[key] = {
                "owner": owner,
                "expires_at": time.monotonic() + ttl_seconds,
                "revoked": False,
            }

        return key

    def validate_key(self, key) -> bool:
        with self._lock:
            record = self._keys.get(key)
            if record is None:
                return False

            return (
                not record["revoked"]
                and time.monotonic() < record["expires_at"]
            )

    def revoke_key(self, key) -> bool:
        with self._lock:
            record = self._keys.get(key)
            if record is None or record["revoked"]:
                return False

            record["revoked"] = True
            return True