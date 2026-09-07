import secrets
import time

class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._otp_lifetime = 300
        self._max_attempts = 5
    
    def generate_otp(self, user_id) -> str:
        otp_value = secrets.randbelow(1000000)
        otp_str = str(otp_value).zfill(6)
        
        self._otps[user_id] = {
            'otp': otp_str,
            'created_at': time.time(),
            'used': False,
            'attempts': 0
        }
        
        return otp_str
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self._otps:
            return False
        
        otp_data = self._otps[user_id]
        
        if otp_data['attempts'] >= self._max_attempts:
            return False
        
        if not isinstance(otp, str) or not otp.isdigit() or len(otp) != 6:
            otp_data['attempts'] += 1
            return False
        
        current_time = time.time()
        if current_time - otp_data['created_at'] > self._otp_lifetime:
            otp_data['attempts'] += 1
            return False
        
        if otp_data['used']:
            otp_data['attempts'] += 1
            return False
        
        if otp != otp_data['otp']:
            otp_data['attempts'] += 1
            return False
        
        otp_data['used'] = True
        return True
