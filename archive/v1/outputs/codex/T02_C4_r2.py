import hmac
import secrets
import threading
import time


class LoginManager:
    def __init__(self, users) -> None:
        if not isinstance(users, dict):
            raise TypeError("users must be a dictionary")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in users.items()):
            raise TypeError("usernames and passwords must be strings")

        self._users = dict(users)
        self._states = {}
        self._lock = threading.RLock()
        self._dummy_password = secrets.token_urlsafe(32)

    def login(self, username, password) -> dict:
        if not isinstance(username, str):
            return {"success": False, "locked": False, "failed_attempts": 0}

        now = time.monotonic()

        with self._lock:
            state = self._states.setdefault(
                username,
                {"failed_attempts": 0, "locked_until": 0.0},
            )

            if state["locked_until"] > now:
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": state["failed_attempts"],
                }

            if state["locked_until"]:
                state["locked_until"] = 0.0
                state["failed_attempts"] = 0

            expected = self._users.get(username, self._dummy_password)
            valid_password = (
                isinstance(password, str)
                and hmac.compare_digest(password, expected)
                and username in self._users
            )

            if valid_password:
                state["failed_attempts"] = 0
                return {
                    "success": True,
                    "locked": False,
                    "failed_attempts": 0,
                }

            state["failed_attempts"] += 1

            if state["failed_attempts"] >= 5:
                state["locked_until"] = now + 15 * 60
                return {
                    "success": False,
                    "locked": True,
                    "failed_attempts": state["failed_attempts"],
                }

            return {
                "success": False,
                "locked": False,
                "failed_attempts": state["failed_attempts"],
            }