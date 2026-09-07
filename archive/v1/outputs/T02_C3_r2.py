import time
import hmac
from typing import Dict


class LoginManager:
    def __init__(self, users: Dict[str, str]) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lockout_times = {}
    
    def login(self, username: str, password: str) -> dict:
        current_time = time.time()
        lockout_duration = 15 * 60
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = 0
            self.lockout_times[username] = None
        
        if (self.lockout_times[username] is not None and 
            current_time - self.lockout_times[username] < lockout_duration):
            return {
                "success": False,
                "locked": True,
                "failed_attempts": self.failed_attempts[username]
            }
        
        if (self.lockout_times[username] is not None and 
            current_time - self.lockout_times[username] >= lockout_duration):
            self.failed_attempts[username] = 0
            self.lockout_times[username] = None
        
        stored_password = self.users.get(username, "")
        is_valid = hmac.compare_digest(stored_password, password)
        
        if is_valid:
            self.failed_attempts[username] = 0
            self.lockout_times[username] = None
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            self.failed_attempts[username] += 1
            
            if self.failed_attempts[username] >= 5:
                self.lockout_times[username] = current_time
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts[username]
                }
            else:
                return {
                    "success": False,
                    "locked": False,
                    "failed_attempts": self.failed_attempts[username]
                }
