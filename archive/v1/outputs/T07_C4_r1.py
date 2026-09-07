import secrets
import time
import hashlib

class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if not isinstance(owner, str) or not owner:
            raise ValueError("Owner must be a non-empty string")
        if not isinstance(ttl_seconds, (int, float)) or ttl_seconds <= 0:
            raise ValueError("TTL must be a positive number")
        
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        expiration_time = time.time() + ttl_seconds
        self._keys[key_hash] = (owner, expiration_time, False)
        
        return key
    
    def validate_key(self, key) -> bool:
        try:
            if not isinstance(key, str) or not key:
                return False
            
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            if key_hash not in self._keys:
                return False
            
            owner, expiration_time, is_revoked = self._keys[key_hash]
            
            if is_revoked or time.time() > expiration_time:
                return False
            
            return True
        except Exception:
            return False
    
    def revoke_key(self, key) -> bool:
        try:
            if not isinstance(key, str) or not key:
                return False
            
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            if key_hash not in self._keys:
                return False
            
            owner, expiration_time, _ = self._keys[key_hash]
            self._keys[key_hash] = (owner, expiration_time, True)
            
            return True
        except Exception:
            return False
