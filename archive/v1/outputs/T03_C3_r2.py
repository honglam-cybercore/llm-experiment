import secrets
import time

class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._token_expiration_seconds = 30 * 60

    def generate_token(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id cannot be None")
        
        token = secrets.token_urlsafe(32)
        
        self._tokens[token] = {
            'user_id': user_id,
            'created_at': time.time(),
            'used': False
        }
        
        return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token:
            return False
        
        if token not in self._tokens:
            return False
        
        token_data = self._tokens[token]
        
        if token_data['used']:
            return False
        
        current_time = time.time()
        if current_time - token_data['created_at'] > self._token_expiration_seconds:
            return False
        
        token_data['used'] = True
        
        return True
