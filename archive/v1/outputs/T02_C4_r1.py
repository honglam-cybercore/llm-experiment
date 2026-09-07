from datetime import datetime, timedelta
import secrets


class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.lockout_times = {}
    
    def login(self, username, password) -> dict:
        if not isinstance(username, str) or not isinstance(password, str):
            return {
                "success": False,
                "locked": False,
                "failed_attempts": 0
            }
        
        current_time = datetime.now()
        
        if username in self.lockout_times:
            lockout_started = self.lockout_times[username]
            lockout_expires = lockout_started + timedelta(minutes=15)
            
            if current_time < lockout_expires:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                del self.lockout_times[username]
                self.failed_attempts[username] = 0
        
        if username in self.users and secrets.compare_digest(self.users[username], password):
            self.failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            current_failed = self.failed_attempts[username]
            
            if current_failed >= 5:
                self.lockout_times[username] = current_time
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": current_failed
                }
            else:
                return {
                    "success": False,
                    "locked": False,
                    "failed_attempts": current_failed
                }
