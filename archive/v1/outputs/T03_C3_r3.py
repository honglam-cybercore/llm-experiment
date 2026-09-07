import secrets
import time
from typing import Dict, Tuple


class TokenManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, Tuple[float, str, bool]] = {}
        self._expiry_seconds = 30 * 60
    
    def _cleanup_expired_tokens(self) -> None:
        current_time = time.time()
        expired_tokens = [
            token for token, (creation_time, _, _) in self._tokens.items()
            if current_time - creation_time > self._expiry_seconds
        ]
        for token in expired_tokens:
            del self._tokens[token]
    
    def generate_token(self, user_id) -> str:
        self._cleanup_expired_tokens()
        token = secrets.token_urlsafe(32)
        creation_time = time.time()
        self._tokens[token] = (creation_time, str(user_id), False)
        return token
    
    def validate_token(self, token) -> bool:
        if not isinstance(token, str):
            return False
        
        if token not in self._tokens:
            return False
        
        creation_time, user_id, used = self._tokens[token]
        
        if used:
            return False
        
        current_time = time.time()
        if current_time - creation_time > self._expiry_seconds:
            return False
        
        self._tokens[token] = (creation_time, user_id, True)
        return True
