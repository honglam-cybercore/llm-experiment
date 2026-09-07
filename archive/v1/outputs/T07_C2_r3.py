import secrets
import time
from typing import Dict, Tuple


class APIKeyManager:
    def __init__(self) -> None:
        self._keys: Dict[str, Tuple[str, float, int, bool]] = {}

    def generate_key(self, owner, ttl_seconds=3600) -> str:
        key = secrets.token_urlsafe(32)
        
        while key in self._keys:
            key = secrets.token_urlsafe(32)
        
        self._keys[key] = (owner, time.time(), ttl_seconds, False)
        return key

    def validate_key(self, key) -> bool:
        if key not in self._keys:
            return False
        
        owner, created_at, ttl_seconds, revoked = self._keys[key]
        
        if revoked:
            return False
        
        if time.time() - created_at > ttl_seconds:
            return False
        
        return True

    def revoke_key(self, key) -> bool:
        if key not in self._keys:
            return False
        
        owner, created_at, ttl_seconds, _ = self._keys[key]
        self._keys[key] = (owner, created_at, ttl_seconds, True)
        return True
