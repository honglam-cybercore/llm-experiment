import random
import time
from typing import Dict, Any


class OTPManager:
    def __init__(self) -> None:
        self.otps: Dict[str, Dict[str, Any]] = {}
    
    def generate_otp(self, user_id) -> str:
        otp = str(random.randint(100000, 999999))
        self.otps[user_id] = {
            'otp': otp,
            'timestamp': time.time(),
            'used': False,
            'failed_attempts': 0
        }
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self.otps:
            return False
        
        otp_data = self.otps[user_id]
        
        if otp_data['failed_attempts'] >= 5:
            return False
        
        if not isinstance(otp, str) or len(otp) != 6 or not otp.isdigit():
            otp_data['failed_attempts'] += 1
            return False
        
        if time.time() - otp_data['timestamp'] > 300:
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
