import secrets
import time
from typing import Dict

class OTPManager:
    def __init__(self) -> None:
        self._otps: Dict[str, Dict] = {}
        self._expiration_time = 300
        self._max_attempts = 5
    
    def _cleanup_expired(self) -> None:
        current_time = time.time()
        expired_users = [
            user_id for user_id, otp_data in self._otps.items()
            if current_time - otp_data['created_at'] > self._expiration_time
        ]
        for user_id in expired_users:
            del self._otps[user_id]
    
    def generate_otp(self, user_id) -> str:
        user_id = str(user_id)
        self._cleanup_expired()
        otp = str(secrets.randbelow(1000000)).zfill(6)
        self._otps[user_id] = {
            'otp': otp,
            'created_at': time.time(),
            'attempts': 0,
            'used': False
        }
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        try:
            user_id = str(user_id)
            otp = str(otp).strip()
        except Exception:
            return False
        
        if not otp or not otp.isdigit() or len(otp) != 6:
            return False
        
        if user_id not in self._otps:
            return False
        
        otp_data = self._otps[user_id]
        
        if otp_data['used']:
            return False
        
        if otp_data['attempts'] >= self._max_attempts:
            return False
        
        current_time = time.time()
        if current_time - otp_data['created_at'] > self._expiration_time:
            return False
        
        if not secrets.compare_digest(otp_data['otp'], otp):
            otp_data['attempts'] += 1
            return False
        
        otp_data['used'] = True
        return True
