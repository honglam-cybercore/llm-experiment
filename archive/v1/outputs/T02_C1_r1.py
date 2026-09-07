import time

class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lock_times = {}
        self.lock_duration = 15 * 60
        self.max_failed_attempts = 5
    
    def login(self, username, password) -> dict:
        if username in self.lock_times:
            if time.time() - self.lock_times[username] < self.lock_duration:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                del self.lock_times[username]
                self.failed_attempts[username] = 0
        
        if username in self.users and self.users[username] == password:
            self.failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            if username not in self.failed_attempts:
                self.failed_attempts[username] = 0
            
            self.failed_attempts[username] += 1
            
            if self.failed_attempts[username] >= self.max_failed_attempts:
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
