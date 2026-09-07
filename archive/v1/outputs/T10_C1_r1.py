import string
import secrets
import time

class CodeManager:
    def __init__(self) -> None:
        self.codes = {}
    
    def generate_code(self, user_id) -> str:
        characters = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(characters) for _ in range(8))
        self.codes[user_id] = {
            'code': code,
            'timestamp': time.time(),
            'used': False
        }
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if user_id not in self.codes:
            return False
        
        code_data = self.codes[user_id]
        
        if code_data['code'] != code:
            return False
        
        if code_data['used']:
            return False
        
        if time.time() - code_data['timestamp'] > 600:
            return False
        
        code_data['used'] = True
        return True
