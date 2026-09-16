import time


class LoginManager:
    def __init__(self, users) -> None:
        self._users = dict(users)
        self._failed_attempts = {}
        self._locked_until = {}

    def login(self, username, password) -> dict:
        now = time.monotonic()
        failed_attempts = self._failed_attempts.get(username, 0)
        locked_until = self._locked_until.get(username, 0.0)

        if now < locked_until:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": failed_attempts,
            }

        if username in self._users and self._users[username] == password:
            self._failed_attempts[username] = 0
            self._locked_until.pop(username, None)
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