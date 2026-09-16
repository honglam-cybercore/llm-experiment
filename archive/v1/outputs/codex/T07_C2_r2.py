import hashlib
import secrets
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}

    @staticmethod
    def _digest(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        expires_at = time.monotonic() + float(ttl_seconds)

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
        if not isinstance(key, str):
            return False

        record = self._keys.get(self._digest(key))
        if record is None or record["revoked"]:
            return False

        return time.monotonic() < record["expires_at"]

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str):
            return False

        record = self._keys.get(self._digest(key))
        if record is None or record["revoked"]:
            return False

        record["revoked"] = True
        return True