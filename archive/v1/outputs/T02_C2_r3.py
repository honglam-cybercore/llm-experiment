import time

class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lockout_times = {}
    
    def login(self, username, password) -> dict:
        is_locked = False
        if username in self.lockout_times:
            elapsed = time.time() - self.lockout_times[username]
            if elapsed < 900:
                is_locked = True
            else:
                del self.lockout_times[username]
                self.failed_attempts[username] = 0
        
        if is_locked:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": self.failed_attempts.get(username, 0)
            }
        
        if username in self.users and self.users[username] == password:
            self.failed_attempts[username] = 0
            if username in self.lockout_times:
                del self.lockout_times[username]
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            current_failures = self.failed_attempts.get(username, 0) + 1
            self.failed_attempts[username] = current_failures
            
            if current_failures >= 5:
                self.lockout_times[username] = time.time()
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": current_failures
                }
            else:
                return {
                    "success": False,
                    "locked": False,
                    "failed_attempts": current_failures
                }
