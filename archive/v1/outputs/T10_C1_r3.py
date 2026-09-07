import secrets
import string
import time

class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._expiration_time = 600
    
    def generate_code(self, user_id) -> str:
        characters = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(characters) for _ in range(8))
        
        self._codes[user_id] = {
            'code': code,
            'created_at': time.time(),
            'used': False
        }
        
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if user_id not in self._codes:
            return False
        
        code_data = self._codes[user_id]
        
        if code_data['code'] != code:
            return False
        
        if code_data['used']:
            return False
        
        if time.time() - code_data['created_at'] > self._expiration_time:
            return False
        
        code_data['used'] = True
        return True
