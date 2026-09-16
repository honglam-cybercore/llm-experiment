import time


class LoginManager:
    def __init__(self, users) -> None:
        self._users = dict(users)
        self._state = {}
        self._lock_duration = 15 * 60

    def login(self, username, password) -> dict:
        now = time.time()
        failures, locked_until = self._state.get(username, (0, 0.0))

        if locked_until > now:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": failures,
            }

        if locked_until:
            failures = 0
            locked_until = 0.0

        if username in self._users and self._users[username] == password:
            self._state[username] = (0, 0.0)
            return {
                "success": True,
                "locked": False,
                "failed_attempts": 0,
            }

        failures += 1
        if failures >= 5:
            locked_until = now + self._lock_duration
            self._state[username] = (failures, locked_until)
            return {
                "success": False,
                "locked": True,
                "failed_attempts": failures,
            }

        self._state[username] = (failures, 0.0)
        return {
            "success": False,
            "locked": False,
            "failed_attempts": failures,
        }