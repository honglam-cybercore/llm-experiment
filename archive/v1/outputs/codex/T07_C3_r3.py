import hashlib
import math
import secrets
import threading
import time
from dataclasses import dataclass
from numbers import Real
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
        return hashlib.sha256(key.encode("ascii")).digest()

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, Real):
            raise TypeError("ttl_seconds must be a finite number")
        if not math.isfinite(float(ttl_seconds)) or ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative and finite")

        key = "ak_" + secrets.token_urlsafe(32)
        record = _APIKeyRecord(
            owner=owner,
            expires_at=time.monotonic() + float(ttl_seconds),
        )

        with self._lock:
            self._keys[self._digest(key)] = record

        return key

    def validate_key(self, key) -> bool:
        if type(key) is not str or len(key) > 256:
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
        if type(key) is not str or len(key) > 256:
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