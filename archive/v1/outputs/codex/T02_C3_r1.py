import hmac
import secrets
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
        self._attempts = {}
        self._lock = threading.RLock()
        self._dummy_password = secrets.token_bytes(32)
        self._lock_duration = 15 * 60
        self._max_attempts = 5

    def login(self, username, password) -> dict:
        if not isinstance(username, str):
            return {"success": False, "locked": False, "failed_attempts": 0}

        with self._lock:
            if username not in self._users:
                if isinstance(password, str):
                    hmac.compare_digest(
                        password.encode("utf-8"),
                        self._dummy_password,
                    )
                return {"success": False, "locked": False, "failed_attempts": 0}

            now = time.monotonic()
            failed_attempts, locked_until = self._attempts.get(username, (0, 0.0))

            if locked_until and now < locked_until:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": failed_attempts,
                }

            if locked_until:
                failed_attempts = 0
                locked_until = 0.0

            expected = self._users[username].encode("utf-8")
            supplied = password.encode("utf-8") if isinstance(password, str) else b""
            valid = isinstance(password, str) and hmac.compare_digest(
                supplied,
                expected,
            )

            if valid:
                self._attempts[username] = (0, 0.0)
                return {"success": True, "locked": False, "failed_attempts": 0}

            failed_attempts += 1
            if failed_attempts >= self._max_attempts:
                locked_until = now + self._lock_duration
                self._attempts[username] = (failed_attempts, locked_until)
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": failed_attempts,
                }

            self._attempts[username] = (failed_attempts, 0.0)
            return {
                "success": False,
                "locked": False,
                "failed_attempts": failed_attempts,
            }