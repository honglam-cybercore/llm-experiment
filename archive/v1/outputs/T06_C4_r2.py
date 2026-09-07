import secrets
import hashlib
import time

class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._expiration_seconds = 300
        self._max_attempts = 5
    
    def generate_otp(self, user_id) -> str:
        otp = str(secrets.randbelow(1000000)).zfill(6)
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        
        self._otps[user_id] = {
            'otp_hash': otp_hash,
            'created_at': time.time(),
            'used': False,
            'failed_attempts': 0
        }
        
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self._otps:
            return False
        
        otp_data = self._otps[user_id]
        
        if otp_data['failed_attempts'] >= self._max_attempts:
            return False
        
        if not isinstance(otp, str) or not otp.isdigit() or len(otp) != 6:
            otp_data['failed_attempts'] += 1
            return False
        
        if time.time() - otp_data['created_at'] > self._expiration_seconds:
            otp_data['failed_attempts'] += 1
            return False
        
        if otp_data['used']:
            otp_data['failed_attempts'] += 1
            return False
        
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        if otp_hash != otp_data['otp_hash']:
            otp_data['failed_attempts'] += 1
            return False
        
        otp_data['used'] = True
        return True
