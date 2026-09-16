import hashlib
import hmac
import secrets
import threading
import time


class LoginManager:
    def __init__(self, users) -> None:
        if not isinstance(users, dict):
            raise TypeError("users must be a dictionary")

        validated_users = {}
        for username, password in users.items():
            if (
                not isinstance(username, str)
                or not isinstance(password, str)
                or len(username) > 256
                or len(password) > 4096
            ):
                raise ValueError("users must map strings to strings")
            validated_users[username] = password

        self._users = validated_users
        self._attempts = {}
        self._lock = threading.RLock()
        self._dummy_password = secrets.token_urlsafe(32)

    def login(self, username, password) -> dict:
        if not isinstance(username, str) or len(username) > 256:
            return {"success": False, "locked": False, "failed_attempts": 0}

        with self._lock:
            failed_attempts, lock_until = self._attempts.get(username, (0, 0.0))
            now = time.monotonic()

            if lock_until > now:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": failed_attempts,
                }

            if lock_until and lock_until <= now:
                failed_attempts = 0
                lock_until = 0.0

            stored_password = self._users.get(username, self._dummy_password)
            valid_password = (
                isinstance(password, str)
                and len(password) <= 4096
                and hmac.compare_digest(password, stored_password)
                and username in self._users
            )

            if valid_password:
                self._attempts.pop(username, None)
                return {"success": True, "locked": False, "failed_attempts": 0}

            failed_attempts += 1
            if failed_attempts >= 5:
                failed_attempts = 5
                lock_until = now + 900.0
                locked = True
            else:
                locked = False

            self._attempts[username] = (failed_attempts, lock_until)
            return {
                "success": False,
                "locked": locked,
                "failed_attempts": failed_attempts,
            }