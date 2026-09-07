import time
import secrets


class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lockout_times = {}
        self.lockout_duration = 15 * 60
    
    def login(self, username, password) -> dict:
        if not isinstance(username, str) or not isinstance(password, str):
            return {
                "success": False,
                "locked": False,
                "failed_attempts": 0
            }
        
        if username not in self.users:
            return {
                "success": False,
                "locked": False,
                "failed_attempts": 0
            }
        
        current_time = time.time()
        
        if username in self.lockout_times:
            lockout_time = self.lockout_times[username]
            if current_time < lockout_time + self.lockout_duration:
                failed_count = self.failed_attempts.get(username, 0)
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": failed_count
                }
            else:
                del self.lockout_times[username]
                self.failed_attempts[username] = 0
        
        if secrets.compare_digest(password, self.users[username]):
            self.failed_attempts[username] = 0
            if username in self.lockout_times:
                del self.lockout_times[username]
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            failed_count = self.failed_attempts[username]
            
            if failed_count >= 5:
                self.lockout_times[username] = current_time
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": failed_count
                }
            else:
                return {
                    "success": False,
                    "locked": False,
                    "failed_attempts": failed_count
                }
