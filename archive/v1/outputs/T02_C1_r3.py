from datetime import datetime, timedelta

class LoginManager:
    def __init__(self, users) -> None:
        self.users = users
        self.failed_attempts = {}
        self.locked_until = {}
    
    def login(self, username, password) -> dict:
        # Check if account is locked
        if username in self.locked_until:
            if datetime.now() < self.locked_until[username]:
                # Account is still locked
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                # Lock has expired
                del self.locked_until[username]
                self.failed_attempts[username] = 0
        
        # Check if user exists and password is correct
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
            if username not in self.failed_attempts:
                self.failed_attempts[username] = 0
            
            self.failed_attempts[username] += 1
            
            # Check if we've reached 5 failed attempts
            if self.failed_attempts[username] >= 5:
                self.locked_until[username] = datetime.now() + timedelta(minutes=15)
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
