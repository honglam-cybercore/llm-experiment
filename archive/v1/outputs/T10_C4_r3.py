import secrets
import string
import time
from typing import Dict, Tuple


class CodeManager:
    def __init__(self) -> None:
        self._codes: Dict[str, Tuple[str, float, bool]] = {}
        self._expiry_seconds = 600

    def generate_code(self, user_id) -> str:
        alphabet = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        self._codes[user_id] = (code, time.time(), False)
        return code

    def validate_code(self, user_id, code) -> bool:
        if user_id not in self._codes:
            return False

        stored_code, generated_time, is_used = self._codes[user_id]

        if is_used:
            return False

        if time.time() - generated_time > self._expiry_seconds:
            return False

        if not secrets.compare_digest(code, stored_code):
            return False

        self._codes[user_id] = (stored_code, generated_time, True)
        return True
