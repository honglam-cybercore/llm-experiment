import secrets
import time


class APIKeyManager:
    def __init__(self) -> None:
        self._keys = {}
    
    def generate_key(self, owner, ttl_seconds=3600) -> str:
        key = secrets.token_urlsafe(32)
        while key in self._keys:
            key = secrets.token_urlsafe(32)
        
        self._keys[key] = {
            'owner': owner,
            'expiry_time': time.time() + ttl_seconds,
            'revoked': False
        }
        
        return key
    
    def validate_key(self, key) -> bool:
        if key not in self._keys:
            return False
        
        key_data = self._keys[key]
        
        if key_data['revoked']:
            return False
        
        if time.time() > key_data['expiry_time']:
            return False
        
        return True
    
    def revoke_key(self, key) -> bool:
        if key not in self._keys:
            return False
        
        self._keys[key]['revoked'] = True
        return True
