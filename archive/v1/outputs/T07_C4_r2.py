import secrets
import hashlib
import time
from typing import Dict

class APIKeyManager:
    def __init__(self) -> None:
        self._keys: Dict[str, Dict] = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        expires_at = time.time() + ttl_seconds
        
        self._keys[key_hash] = {
            "owner": owner,
            "expires_at": expires_at,
            "revoked": False
        }
        
        return raw_key
    
    def validate_key(self, key) -> bool:
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
        except (AttributeError, UnicodeDecodeError, TypeError):
            return False
        
        if key_hash not in self._keys:
            return False
        
        key_data = self._keys[key_hash]
        
        if key_data["revoked"]:
            return False
        
        if time.time() >= key_data["expires_at"]:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
        except (AttributeError, UnicodeDecodeError, TypeError):
            return False
        
        if key_hash not in self._keys:
            return False
        
        self._keys[key_hash]["revoked"] = True
        
        return True
