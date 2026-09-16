import time


class LoginManager:
    def __init__(self, users) -> None:
        self.users = dict(users)
        self._failed_attempts = {username: 0 for username in self.users}
        self._locked_until = {}

    def login(self, username, password) -> dict:
        now = time.time()
        failed_attempts = self._failed_attempts.get(username, 0)
        locked_until = self._locked_until.get(username, 0)

        if now < locked_until:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": failed_attempts,
            }

        if locked_until:
            self._locked_until.pop(username, None)
            failed_attempts = 0
            self._failed_attempts[username] = 0

        if username in self.users and self.users[username] == password:
            self._failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0,
            }

        failed_attempts += 1
        self._failed_attempts[username] = failed_attempts

        if failed_attempts >= 5:
            self._locked_until[username] = now + 15 * 60
            return {
                "success": False,
                "locked": True,
                "failed_attempts": failed_attempts,
            }

        return {
            "success": False,
            "locked": False,
            "failed_attempts": failed_attempts,
        }