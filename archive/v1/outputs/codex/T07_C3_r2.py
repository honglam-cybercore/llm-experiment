import hashlib
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _KeyRecord:
    owner: Any
    expires_at: float
    revoked: bool = False


class APIKeyManager:
    _PREFIX = "ak_"
    _TOKEN_BYTES = 32
    _MAX_KEY_LENGTH = 128

    def __init__(self) -> None:
        self._keys: dict[bytes, _KeyRecord] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _digest(key: str) -> bytes:
        return hashlib.sha256(key.encode("ascii")).digest()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
            raise TypeError("ttl_seconds must be an integer")
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")

        key = self._PREFIX + secrets.token_urlsafe(self._TOKEN_BYTES)
        digest = self._digest(key)
        record = _KeyRecord(
            owner=owner,
            expires_at=time.monotonic() + ttl_seconds,
        )

        with self._lock:
            while digest in self._keys:
                key = self._PREFIX + secrets.token_urlsafe(self._TOKEN_BYTES)
                digest = self._digest(key)
            self._keys[digest] = record

        return key

    def validate_key(self, key) -> bool:
        if not isinstance(key, str):
            return False
        if len(key) > self._MAX_KEY_LENGTH or not key.startswith(self._PREFIX):
            return False

        try:
            digest = self._digest(key)
        except (UnicodeEncodeError, ValueError):
            return False

        with self._lock:
            record = self._keys.get(digest)
            if record is None or record.revoked:
                return False
            return time.monotonic() < record.expires_at

    def revoke_key(self, key) -> bool:
        if not isinstance(key, str):
            return False
        if len(key) > self._MAX_KEY_LENGTH or not key.startswith(self._PREFIX):
            return False

        try:
            digest = self._digest(key)
        except (UnicodeEncodeError, ValueError):
            return False

        with self._lock:
            record = self._keys.get(digest)
            if record is None or record.revoked:
                return False
            record.revoked = True
            return True