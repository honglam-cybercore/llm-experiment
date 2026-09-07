import time
from typing import Dict


class LoginManager:
    FAILED_ATTEMPTS_THRESHOLD = 5
    LOCKOUT_DURATION = 15 * 60
    
    def __init__(self, users: Dict[str, str]) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lockout_times = {}
    
    def login(self, username: str, password: str) -> dict:
        if not isinstance(username, str) or not isinstance(password, str):
            return {
                "success": False,
                "locked": False,
                "failed_attempts": 0
            }
        
        current_time = time.time()
        
        if username in self.lockout_times:
            if current_time - self.lockout_times[username] < self.LOCKOUT_DURATION:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                del self.lockout_times[username]
                self.failed_attempts[username] = 0
        
        if username in self.users and self.users[username] == password:
            self.failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            
            is_locked = self.failed_attempts[username] >= self.FAILED_ATTEMPTS_THRESHOLD
            if is_locked:
                self.lockout_times[username] = current_time
            
            return {
                "success": False,
                "locked": is_locked,
                "failed_attempts": self.failed_attempts[username]
            }
