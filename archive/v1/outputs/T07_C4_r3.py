import time
import secrets
from typing import Dict, Any


class APIKeyManager:
    def __init__(self) -> None:
        self._keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if not isinstance(owner, str) or not owner:
            raise ValueError("owner must be a non-empty string")
        if not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
        
        key = secrets.token_urlsafe(32)
        
        while key in self._keys:
            key = secrets.token_urlsafe(32)
        
        now = time.time()
        self._keys[key] = {
            'owner': owner,
            'created_at': now,
            'expires_at': now + ttl_seconds,
            'revoked': False
        }
        
        return key
    
    def validate_key(self, key) -> bool:
        if not isinstance(key, str):
            return False
        
        if key not in self._keys:
            return False
        
        key_data = self._keys[key]
        
        if key_data['revoked']:
            return False
        
        if time.time() > key_data['expires_at']:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        if not isinstance(key, str):
            return False
        
        if key not in self._keys:
            return False
        
        self._keys[key]['revoked'] = True
        return True
