import time


class LoginManager:
    def __init__(self, users) -> None:
        self._users = dict(users)
        self._failed_attempts = {}
        self._locked_until = {}

    def login(self, username, password) -> dict:
        now = time.time()
        locked_until = self._locked_until.get(username, 0)

        if now < locked_until:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": self._failed_attempts.get(username, 5),
            }

        if locked_until:
            self._locked_until.pop(username, None)
            self._failed_attempts[username] = 0

        if username in self._users and self._users[username] == password:
            self._failed_attempts[username] = 0
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0,
            }

        attempts = self._failed_attempts.get(username, 0) + 1
        self._failed_attempts[username] = attempts

        if attempts >= 5:
            self._locked_until[username] = now + 15 * 60
            return {
                "success": False,
                "locked": True,
                "failed_attempts": attempts,
            }

        return {
            "success": False,
            "locked": False,
            "failed_attempts": attempts,
        }