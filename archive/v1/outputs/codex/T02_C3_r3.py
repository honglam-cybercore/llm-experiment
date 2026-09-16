import hmac
import secrets
import time


class LoginManager:
    def __init__(self, users) -> None:
        if not isinstance(users, dict):
            raise TypeError("users must be a dict")
        if any(not isinstance(username, str) or not isinstance(password, str)
               for username, password in users.items()):
            raise TypeError("usernames and passwords must be strings")

        self._users = dict(users)
        self._attempts = {}
        self._locked_until = {}
        self._dummy_password = secrets.token_urlsafe(32)

    def login(self, username, password) -> dict:
        if not isinstance(username, str) or not isinstance(password, str):
            return {"success": False, "locked": False, "failed_attempts": 0}

        now = time.monotonic()
        locked_until = self._locked_until.get(username, 0.0)

        if locked_until > now:
            return {
                "success": False,
                "locked": True,
                "failed_attempts": self._attempts.get(username, 5),
            }

        if locked_until:
            self._locked_until.pop(username, None)
            self._attempts.pop(username, None)

        stored_password = self._users.get(username, self._dummy_password)
        valid = username in self._users and hmac.compare_digest(
            stored_password, password
        )

        if valid:
            self._attempts.pop(username, None)
            self._locked_until.pop(username, None)
            return {"success": True, "locked": False, "failed_attempts": 0}

        failed_attempts = self._attempts.get(username, 0) + 1
        self._attempts[username] = failed_attempts

        if failed_attempts >= 5:
            self._attempts[username] = 5
            self._locked_until[username] = now + 15 * 60
            return {"success": False, "locked": True, "failed_attempts": 5}

        return {
            "success": False,
            "locked": False,
            "failed_attempts": failed_attempts,
        }