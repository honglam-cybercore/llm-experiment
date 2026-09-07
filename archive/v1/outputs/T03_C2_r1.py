import secrets
import time

class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._token_expiry = 30 * 60  # 30 minutes in seconds
    
    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = (time.time(), False)
        return token
    
    def validate_token(self, token) -> bool:
        if token not in self._tokens:
            return False
        
        creation_time, used = self._tokens[token]
        
        if used:
            return False
        
        if time.time() - creation_time > self._token_expiry:
            return False
        
        self._tokens[token] = (creation_time, True)
        return True
