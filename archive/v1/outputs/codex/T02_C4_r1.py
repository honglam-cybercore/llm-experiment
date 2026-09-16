import hmac
import threading
import time


class LoginManager:
    def __init__(self, users) -> None:
        if not isinstance(users, dict):
            raise TypeError("users must be a dictionary")

        for username, password in users.items():
            if not isinstance(username, str) or not isinstance(password, str):
                raise TypeError("usernames and passwords must be strings")

        self._users = dict(users)
        self._failed_attempts = {username: 0 for username in self._users}
        self._locked_until = {username: 0.0 for username in self._users}
        self._lock = threading.RLock()
        self._lockout_seconds = 15 * 60
        self._max_failed_attempts = 5

    def login(self, username, password) -> dict:
        if not isinstance(username, str):
            return {"success": False, "locked": False, "failed_attempts": 0}

        with self._lock:
            if username not in self._users:
                return {"success": False, "locked": False, "failed_attempts": 0}

            now = time.monotonic()
            failed_attempts = self._failed_attempts[username]
            locked_until = self._locked_until[username]

            if locked_until > now:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": failed_attempts,
                }

            if locked_until:
                self._locked_until[username] = 0.0

            valid_password = (
                isinstance(password, str)
                and hmac.compare_digest(password, self._users[username])
            )

            if valid_password:
                self._failed_attempts[username] = 0
                return {"success": True, "locked": False, "failed_attempts": 0}

            failed_attempts = min(
                failed_attempts + 1,
                self._max_failed_attempts,
            )
            self._failed_attempts[username] = failed_attempts

            if failed_attempts >= self._max_failed_attempts:
                self._locked_until[username] = (
                    now + self._lockout_seconds
                )
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