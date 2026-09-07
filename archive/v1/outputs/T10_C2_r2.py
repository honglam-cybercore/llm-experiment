import secrets
import string
import time


class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._expiration_time = 600

    def generate_code(self, user_id) -> str:
        code = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        self._codes[user_id] = (code, time.time(), False)
        return code

    def validate_code(self, user_id, code) -> bool:
        if user_id not in self._codes:
            return False

        stored_code, generation_time, used = self._codes[user_id]

        if code != stored_code:
            return False

        if used:
            return False

        if time.time() - generation_time > self._expiration_time:
            return False

        self._codes[user_id] = (stored_code, generation_time, True)

        return True
