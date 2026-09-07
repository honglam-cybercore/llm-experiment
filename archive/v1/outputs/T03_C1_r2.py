import time
import uuid

class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
    
    def generate_token(self, user_id) -> str:
        token = str(uuid.uuid4())
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
        
        if time.time() - token_data['created_at'] > 1800:
            return False
        
        if token_data['used']:
            return False
        
        token_data['used'] = True
        return True
