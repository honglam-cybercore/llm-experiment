import time
import hmac
from typing import Dict


class LoginManager:
    def __init__(self, users: Dict[str, str]) -> None:
        self.users = users
        self.failed_attempts: Dict[str, int] = {}
        self.locked_until: Dict[str, float] = {}
        self.lock_duration = 15 * 60
        self.max_failed_attempts = 5
    
    def login(self, username: str, password: str) -> dict:
        if not isinstance(username, str) or not isinstance(password, str):
            return {
                "success": False,
                "locked": False,
                "failed_attempts": 0
            }
        
        current_time = time.time()
        
        if username in self.locked_until:
            if current_time < self.locked_until[username]:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                del self.locked_until[username]
                self.failed_attempts[username] = 0
        
        stored_password = self.users.get(username, '')
        password_matches = hmac.compare_digest(password, stored_password)
        
        if username in self.users and password_matches:
            self.failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0
            }
        
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
        failed_count = self.failed_attempts[username]
        
        if failed_count >= self.max_failed_attempts:
            self.locked_until[username] = current_time + self.lock_duration
            return {
                "success": False,
                "locked": True,
                "failed_attempts": failed_count
            }
        
        return {
            "success": False,
            "locked": False,
            "failed_attempts": failed_count
        }
