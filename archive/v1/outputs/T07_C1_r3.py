import secrets
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        key = secrets.token_urlsafe(32)
        self._keys[key] = {
            'owner': owner,
            'created_at': time.time(),
            'ttl_seconds': ttl_seconds,
            'revoked': False
        }
        return key
    
    def validate_key(self, key) -> bool:
        if key not in self._keys:
            return False
        
        key_data = self._keys[key]
        
        if key_data['revoked']:
            return False
        
        elapsed = time.time() - key_data['created_at']
        if elapsed > key_data['ttl_seconds']:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        if key not in self._keys:
            return False
        
        self._keys[key]['revoked'] = True
        return True
