import hashlib
import hmac
import secrets
import threading
import time


class LoginManager:
    _LOCKOUT_SECONDS = 15 * 60
    _MAX_USERNAME_LENGTH = 256
    _MAX_PASSWORD_LENGTH = 4096
    _PBKDF2_ITERATIONS = 600_000

    def __init__(self, users) -> None:
        if not isinstance(users, dict):
            raise TypeError("users must be a dictionary")

        self._users = {}
        self._state = {}
        self._lock = threading.RLock()

        for username, password in users.items():
            if (
                not isinstance(username, str)
                or not username
                or len(username) > self._MAX_USERNAME_LENGTH
                or not isinstance(password, str)
                or len(password) > self._MAX_PASSWORD_LENGTH
            ):
                raise ValueError("invalid user credentials")

            salt = secrets.token_bytes(16)
            password_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                self._PBKDF2_ITERATIONS,
            )
            self._users[username] = (salt, password_hash)
            self._state[username] = {"failed_attempts": 0, "locked_until": 0.0}

        self._dummy_salt = secrets.token_bytes(16)
        self._dummy_hash = hashlib.pbkdf2_hmac(
            "sha256",
            secrets.token_bytes(32),
            self._dummy_salt,
            self._PBKDF2_ITERATIONS,
        )

    def login(self, username, password) -> dict:
        if not isinstance(username, str) or len(username) > self._MAX_USERNAME_LENGTH:
            return {"success": False, "locked": False, "failed_attempts": 0}

        with self._lock:
            user_record = self._users.get(username)
            state = self._state.get(username)

            if user_record is None:
                salt, expected_hash = self._dummy_salt, self._dummy_hash
                state = None
            else:
                salt, expected_hash = user_record
                now = time.monotonic()
                if now < state["locked_until"]:
                    return {
                        "success": False,
                        "locked": True,
                        "failed_attempts": state["failed_attempts"],
                    }
                if state["locked_until"]:
                    state["failed_attempts"] = 0
                    state["locked_until"] = 0.0

            valid_password = False
            if isinstance(password, str) and len(password) <= self._MAX_PASSWORD_LENGTH:
                try:
                    candidate_hash = hashlib.pbkdf2_hmac(
                        "sha256",
                        password.encode("utf-8"),
                        salt,
                        self._PBKDF2_ITERATIONS,
                    )
                    valid_password = hmac.compare_digest(candidate_hash, expected_hash)
                except (UnicodeError, ValueError):
                    valid_password = False

            if user_record is not None and valid_password:
                state["failed_attempts"] = 0
                state["locked_until"] = 0.0
                return {"success": True, "locked": False, "failed_attempts": 0}

            if state is None:
                return {"success": False, "locked": False, "failed_attempts": 0}

            state["failed_attempts"] += 1
            if state["failed_attempts"] >= 5:
                state["locked_until"] = time.monotonic() + self._LOCKOUT_SECONDS
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