from datetime import datetime, timedelta

class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lock_times = {}
        self.LOCK_DURATION = timedelta(minutes=15)
        self.MAX_FAILED_ATTEMPTS = 5
    
    def login(self, username, password) -> dict:
        current_time = datetime.now()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = 0
        
        is_locked = False
        if username in self.lock_times:
            lock_time = self.lock_times[username]
            if current_time < lock_time + self.LOCK_DURATION:
                is_locked = True
            else:
                del self.lock_times[username]
        
        if is_locked:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": self.failed_attempts[username]
            }
        
        success = username in self.users and self.users[username] == password
        
        if success:
            self.failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            self.failed_attempts[username] += 1
            
            if self.failed_attempts[username] >= self.MAX_FAILED_ATTEMPTS:
                self.lock_times[username] = current_time
            
            return {
                "success": False,
                "locked": self.failed_attempts[username] >= self.MAX_FAILED_ATTEMPTS,
                "failed_attempts": self.failed_attempts[username]
            }
