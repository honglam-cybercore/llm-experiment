import secrets
import time
from typing import Dict, Tuple

class TokenManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, Tuple[float, str, bool]] = {}
    
    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = (time.time(), user_id, False)
        return token
    
    def validate_token(self, token) -> bool:
        if token not in self._tokens:
            return False
        
        creation_time, user_id, used = self._tokens[token]
        
        if time.time() - creation_time > 1800:
            return False
        
        if used:
            return False
        
        self._tokens[token] = (creation_time, user_id, True)
        return True
