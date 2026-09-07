import random
import string
import time

class CodeManager:
    def __init__(self) -> None:
        self.codes = {}
    
    def generate_code(self, user_id) -> str:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.codes[code] = {
            'user_id': user_id,
            'timestamp': time.time(),
            'used': False
        }
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if code not in self.codes:
            return False
        
        code_data = self.codes[code]
        
        if code_data['user_id'] != user_id:
            return False
        
        if code_data['used']:
            return False
        
        if time.time() - code_data['timestamp'] > 600:
            return False
        
        code_data['used'] = True
        return True
