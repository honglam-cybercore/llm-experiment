import secrets
import hashlib
import time
from typing import Dict, Tuple


class APIKeyManager:
    def __init__(self) -> None:
        # Storage: key_hash -> (owner, created_at, expires_at, revoked)
        self._keys: Dict[str, Tuple[str, float, float, bool]] = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        key = secrets.token_urlsafe(32)
        now = time.time()
        expires_at = now + ttl_seconds
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self._keys[key_hash] = (owner, now, expires_at, False)
        return key
    
    def validate_key(self, key) -> bool:
        if not key:
            return False
        
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
        except Exception:
            return False
        
        if key_hash not in self._keys:
            return False
        
        owner, created_at, expires_at, revoked = self._keys[key_hash]
        
        if revoked or time.time() > expires_at:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        if not key:
            return False
        
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
        except Exception:
            return False
        
        if key_hash not in self._keys:
            return False
        
        owner, created_at, expires_at, revoked = self._keys[key_hash]
        self._keys[key_hash] = (owner, created_at, expires_at, True)
        return True
