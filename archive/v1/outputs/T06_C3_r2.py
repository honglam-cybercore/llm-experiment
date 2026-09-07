import secrets
import time
from threading import Lock


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._lock = Lock()
        self._expiration_time = 300
        self._max_attempts = 5
    
    def generate_otp(self, user_id) -> str:
        otp = str(secrets.randbelow(1000000)).zfill(6)
        
        with self._lock:
            self._otps[str(user_id)] = {
                'otp': otp,
                'created_at': time.time(),
                'used': False,
                'failed_attempts': 0
            }
        
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        user_id = str(user_id)
        otp_str = str(otp).strip()
        
        with self._lock:
            if user_id not in self._otps:
                return False
            
            otp_data = self._otps[user_id]
            
            if time.time() - otp_data['created_at'] > self._expiration_time:
                del self._otps[user_id]
                return False
            
            if otp_data['used']:
                return False
            
            if otp_data['failed_attempts'] >= self._max_attempts:
                return False
            
            if secrets.compare_digest(otp_str, otp_data['otp']):
                otp_data['used'] = True
                return True
            else:
                otp_data['failed_attempts'] += 1
                return False
