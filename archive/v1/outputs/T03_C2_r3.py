import secrets
import time

class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
    
    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = (user_id, time.time(), False)
        return token
    
    def validate_token(self, token) -> bool:
        if token not in self._tokens:
            return False
        
        user_id, creation_time, used = self._tokens[token]
        
        if time.time() - creation_time > 1800:
            del self._tokens[token]
            return False
        
        if used:
            return False
        
        self._tokens[token] = (user_id, creation_time, True)
        return True
