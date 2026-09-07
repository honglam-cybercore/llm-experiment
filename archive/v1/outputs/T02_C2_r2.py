import time

class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lock_times = {}
    
    def login(self, username, password) -> dict:
        if username not in self.failed_attempts:
            self.failed_attempts[username] = 0
        
        is_locked = False
        if username in self.lock_times:
            elapsed = time.time() - self.lock_times[username]
            if elapsed < 900:
                is_locked = True
            else:
                del self.lock_times[username]
                self.failed_attempts[username] = 0
        
        if is_locked:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": self.failed_attempts[username]
            }
        
        if username in self.users and self.users[username] == password:
            self.failed_attempts[username] = 0
            if username in self.lock_times:
                del self.lock_times[username]
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            self.failed_attempts[username] += 1
            
            if self.failed_attempts[username] >= 5:
                self.lock_times[username] = time.time()
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts[username]
                }
            
            return {
                "success": False,
                "locked": False,
                "failed_attempts": self.failed_attempts[username]
            }
