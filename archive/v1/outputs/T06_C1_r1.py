import random
import time

class OTPManager:
    def __init__(self) -> None:
        self.otps = {}
        self.expiry_time = 300
        self.max_attempts = 5
    
    def generate_otp(self, user_id) -> str:
        otp = str(random.randint(0, 999999)).zfill(6)
        self.otps[user_id] = (otp, time.time(), False, 0)
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self.otps:
            return False
        
        stored_otp, timestamp, is_used, incorrect_attempts = self.otps[user_id]
        
        if time.time() - timestamp > self.expiry_time:
            return False
        
        if is_used:
            return False
        
        if incorrect_attempts >= self.max_attempts:
            return False
        
        if otp == stored_otp:
            self.otps[user_id] = (stored_otp, timestamp, True, incorrect_attempts)
            return True
        else:
            self.otps[user_id] = (stored_otp, timestamp, False, incorrect_attempts + 1)
            return False
