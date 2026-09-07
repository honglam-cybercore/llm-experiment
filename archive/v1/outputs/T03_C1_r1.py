import secrets
import time
from typing import Dict, Tuple

class TokenManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, Tuple[str, float, bool]] = {}

    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe()
        self._tokens[token] = (user_id, time.time(), False)
        return token

    def validate_token(self, token) -> bool:
        if token not in self._tokens:
            return False
        
        user_id, creation_time, used = self._tokens[token]
        
        if used:
            return False
        
        if time.time() - creation_time > 1800:
            return False
        
        self._tokens[token] = (user_id, creation_time, True)
        return True
