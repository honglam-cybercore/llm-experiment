import hmac
import time


class LoginManager:
    def __init__(self, users):
        self.users = users
        self.failed_attempts = {}
        self.lockout_times = {}
        self.lockout_duration = 15 * 60

    def login(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            return {
                "success": False,
                "locked": False,
                "failed_attempts": 0
            }

        if username in self.lockout_times:
            elapsed = time.time() - self.lockout_times[username]
            if elapsed < self.lockout_duration:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": self.failed_attempts.get(username, 0)
                }
            else:
                del self.lockout_times[username]
                self.failed_attempts[username] = 0

        stored_password = self.users.get(username, "")

        try:
            password_match = hmac.compare_digest(stored_password, password)
        except TypeError:
            password_match = False

        user_exists = username in self.users
        success = password_match and user_exists

        if success:
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
                self.lockout_times[username] = time.time()
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
