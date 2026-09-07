import random
import time

class OTPManager:
    def __init__(self) -> None:
        self.otps = {}
    
    def generate_otp(self, user_id) -> str:
        otp = str(random.randint(100000, 999999))
        self.otps[user_id] = {
            'otp': otp,
            'created_time': time.time(),
            'used': False,
            'attempts': 0
        }
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self.otps:
            return False
        
        data = self.otps[user_id]
        
        if time.time() - data['created_time'] > 300:
            return False
        
        if data['used']:
            return False
        
        if data['attempts'] >= 5:
            return False
        
        if otp == data['otp']:
            data['used'] = True
            return True
        else:
            data['attempts'] += 1
            return False
