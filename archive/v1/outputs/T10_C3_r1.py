import secrets
import time

class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._expiry_time = 600
    
    def generate_code(self, user_id) -> str:
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        self._codes[code] = (str(user_id), time.time(), False)
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if not isinstance(code, str):
            return False
        
        if code not in self._codes:
            return False
        
        stored_user_id, timestamp, used = self._codes[code]
        
        if str(user_id) != stored_user_id:
            return False
        
        if time.time() - timestamp > self._expiry_time:
            return False
        
        if used:
            return False
        
        self._codes[code] = (stored_user_id, timestamp, True)
        return True
