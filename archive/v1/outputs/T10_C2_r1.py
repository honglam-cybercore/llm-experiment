import secrets
import string
import time

class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._expiry_seconds = 10 * 60
    
    def generate_code(self, user_id) -> str:
        alphabet = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        self._codes[user_id] = (code, time.time(), False)
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if user_id not in self._codes:
            return False
        
        stored_code, timestamp, used = self._codes[user_id]
        
        if used:
            return False
        
        if time.time() - timestamp > self._expiry_seconds:
            return False
        
        if code != stored_code:
            return False
        
        self._codes[user_id] = (stored_code, timestamp, True)
        return True
