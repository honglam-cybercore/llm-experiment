import secrets
import hashlib
import time
from typing import Dict, Tuple

class APIKeyManager:
    def __init__(self) -> None:
        self._keys: Dict[str, Tuple[str, float, int, bool]] = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
        
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self._keys[key_hash] = (str(owner), time.time(), ttl_seconds, False)
        
        return key
    
    def validate_key(self, key) -> bool:
        if not isinstance(key, str) or not key:
            return False
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self._keys:
            return False
        
        owner, created_at, ttl_seconds, revoked = self._keys[key_hash]
        
        if revoked:
            return False
        
        if time.time() - created_at > ttl_seconds:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        if not isinstance(key, str) or not key:
            return False
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self._keys:
            return False
        
        owner, created_at, ttl_seconds, revoked = self._keys[key_hash]
        
        if revoked:
            return False
        
        self._keys[key_hash] = (owner, created_at, ttl_seconds, True)
        return True
