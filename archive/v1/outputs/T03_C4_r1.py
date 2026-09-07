import secrets
import time

class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._expiration_seconds = 30 * 60
    
    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = {
            'user_id': user_id,
            'created_at': time.time(),
            'used': False
        }
        return token
    
    def validate_token(self, token) -> bool:
        try:
            if token not in self._tokens:
                return False
        except TypeError:
            return False
        
        token_data = self._tokens[token]
        
        if token_data['used']:
            return False
        
        if time.time() - token_data['created_at'] > self._expiration_seconds:
            return False
        
        token_data['used'] = True
        return True
