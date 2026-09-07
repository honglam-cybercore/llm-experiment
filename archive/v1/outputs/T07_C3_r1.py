import secrets
import time

class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        if not owner or not isinstance(owner, str):
            raise ValueError("owner must be a non-empty string")
        if not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
        
        key = secrets.token_urlsafe(32)
        
        self._keys[key] = {
            'owner': owner,
            'created_at': time.time(),
            'ttl_seconds': ttl_seconds,
            'revoked': False
        }
        
        return key
    
    def validate_key(self, key) -> bool:
        if not key or not isinstance(key, str):
            return False
        
        if key not in self._keys:
            return False
        
        metadata = self._keys[key]
        
        if metadata['revoked']:
            return False
        
        current_time = time.time()
        expiration_time = metadata['created_at'] + metadata['ttl_seconds']
        if current_time > expiration_time:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        if not key or not isinstance(key, str):
            return False
        
        if key not in self._keys:
            return False
        
        self._keys[key]['revoked'] = True
        return True
