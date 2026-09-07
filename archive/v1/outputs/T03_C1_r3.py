import secrets
import time


class TokenManager:
    def __init__(self) -> None:
        self._tokens: dict = {}
    
    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = {
            'user_id': user_id,
            'created_at': time.time(),
            'used': False
        }
        return token
    
    def validate_token(self, token) -> bool:
        if token not in self._tokens:
            return False
        
        token_data = self._tokens[token]
        
        if token_data['used']:
            return False
        
        if time.time() - token_data['created_at'] > 1800:
            return False
        
        token_data['used'] = True
        return True
