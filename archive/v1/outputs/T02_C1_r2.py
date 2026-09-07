from datetime import datetime, timedelta


class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.locked_until = {}
    
    def login(self, username, password) -> dict:
        current_time = datetime.now()
        
        # Check if account is locked and if lock has expired
        if username in self.locked_until:
            if current_time < self.locked_until[username]:
                # Still locked
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                # Lock has expired, reset it
                del self.locked_until[username]
                self.failed_attempts[username] = 0
        
        # Check if username exists and password matches
        if username in self.users and self.users[username] == password:
            # Successful login
            self.failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        else:
            # Failed login
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            is_locked = False
            
            # Check if we need to lock the account
            if self.failed_attempts[username] >= 5:
                self.locked_until[username] = current_time + timedelta(minutes=15)
                is_locked = True
            
            return {
                "success": False,
                "locked": is_locked,
                "failed_attempts": self.failed_attempts[username]
            }
