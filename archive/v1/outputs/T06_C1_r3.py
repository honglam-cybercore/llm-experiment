import random
import time

class OTPManager:
    def __init__(self) -> None:
        self.otps = {}
        self.timestamps = {}
        self.used = {}
        self.attempts = {}
    
    def generate_otp(self, user_id) -> str:
        otp = ''.join(random.choices('0123456789', k=6))
        self.otps[user_id] = otp
        self.timestamps[user_id] = time.time()
        self.used[user_id] = False
        self.attempts[user_id] = 0
        return otp
    
    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self.otps:
            return False
        
        if self.attempts[user_id] >= 5:
            return False
        
        if self.used[user_id]:
            return False
        
        if time.time() - self.timestamps[user_id] > 300:
            return False
        
        if self.otps[user_id] == otp:
            self.used[user_id] = True
            return True
        else:
            self.attempts[user_id] += 1
            return False
