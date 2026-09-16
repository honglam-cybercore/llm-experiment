import hashlib
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _APIKeyRecord:
    owner: Any
    expires_at: float
    revoked: bool = False


class APIKeyManager:
    def __init__(self) -> None:
        self._keys: dict[bytes, _APIKeyRecord] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _digest(key: str) -> bytes:
        return hashlib.sha256(key.encode("utf-8")).digest()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
            raise TypeError("ttl_seconds must be an integer")
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must not be negative")

        with self._lock:
            while True:
                key = secrets.token_urlsafe(32)
                digest = self._digest(key)
                if digest not in self._keys:
                    self._keys[digest] = _APIKeyRecord(
                        owner=owner,
                        expires_at=time.monotonic() + ttl_seconds,
                    )
                    return key

    def validate_key(self, key) -> bool:
        if not isinstance(key, str) or not key or len(key) > 1024:
            return False

        digest = self._digest(key)
        with self._lock:
            record = self._keys.get(digest)
            if record is None or record.revoked:
                return False
            return time.monotonic() < record.expires_at

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str) or not key or len(key) > 1024:
            return False

        digest = self._digest(key)
        with self._lock:
            record = self._keys.get(digest)
            if record is None or record.revoked:
                return False
            record.revoked = True
            return True