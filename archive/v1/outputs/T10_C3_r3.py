import secrets
import time
from typing import Dict, Tuple

class CodeManager:
    def __init__(self) -> None:
        self._codes: Dict[str, Tuple[str, float, bool]] = {}
        self._expiration_time = 600
    
    def generate_code(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id cannot be None")
        
        user_id = str(user_id)
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        self._codes[user_id] = (code, time.time(), False)
        
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if user_id is None or code is None:
            return False
        
        user_id = str(user_id)
        
        if user_id not in self._codes:
            return False
        
        stored_code, timestamp, used = self._codes[user_id]
        
        if used:
            return False
        
        if time.time() - timestamp > self._expiration_time:
            del self._codes[user_id]
            return False
        
        if not secrets.compare_digest(stored_code, str(code)):
            return False
        
        self._codes[user_id] = (stored_code, timestamp, True)
        
        return True
