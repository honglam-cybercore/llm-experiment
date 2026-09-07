import secrets
import time
import hashlib
from typing import Dict, Tuple

class OTPManager:
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    MAX_FAILED_ATTEMPTS = 5
    
    def __init__(self) -> None:
        self._otps: Dict[str, Tuple[str, float, bool, int]] = {}
    
    def generate_otp(self, user_id) -> str:
        otp_value = secrets.randbelow(10 ** self.OTP_LENGTH)
        otp_str = str(otp_value).zfill(self.OTP_LENGTH)
        
        otp_hash = hashlib.sha256(otp_str.encode()).hexdigest()
        current_time = time.time()
        self._otps[user_id] = (otp_hash, current_time, False, 0)
        
        return otp_str
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self._otps:
            return False
        
        otp_hash, timestamp, used, failed_attempts = self._otps[user_id]
        
        if failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            return False
        
        if not isinstance(otp, str) or not otp.isdigit() or len(otp) != self.OTP_LENGTH:
            return False
        
        current_time = time.time()
        if current_time - timestamp > self.OTP_EXPIRY_MINUTES * 60:
            return False
        
        if used:
            return False
        
        provided_hash = hashlib.sha256(otp.encode()).hexdigest()
        if provided_hash != otp_hash:
            self._otps[user_id] = (otp_hash, timestamp, used, failed_attempts + 1)
            return False
        
        self._otps[user_id] = (otp_hash, timestamp, True, failed_attempts)
        return True
