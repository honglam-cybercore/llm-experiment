import random
import time

class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
    
    def generate_otp(self, user_id) -> str:
        otp = str(random.randint(100000, 999999))
        self._otps[user_id] = {
            'otp': otp,
            'created_at': time.time(),
            'used': False,
            'failed_attempts': 0
        }
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self._otps:
            return False
        
        otp_data = self._otps[user_id]
        
        if otp_data['failed_attempts'] >= 5:
            return False
        
        if not isinstance(otp, str) or not otp.isdigit() or len(otp) != 6:
            otp_data['failed_attempts'] += 1
            return False
        
        if time.time() - otp_data['created_at'] > 300:
            otp_data['failed_attempts'] += 1
            return False
        
        if otp_data['used']:
            otp_data['failed_attempts'] += 1
            return False
        
        if otp != otp_data['otp']:
            otp_data['failed_attempts'] += 1
            return False
        
        otp_data['used'] = True
        return True
