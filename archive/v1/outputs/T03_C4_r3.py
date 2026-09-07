import secrets
import time
from typing import Dict


class TokenManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, float] = {}
        self._expiration_seconds = 30 * 60

    def generate_token(self, user_id) -> str:
        if user_id is None:
            raise ValueError("user_id cannot be None")

        token = secrets.token_urlsafe(32)
        self._tokens[token] = time.time()
        return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token:
            return False

        if token not in self._tokens:
            return False

        creation_time = self._tokens[token]
        current_time = time.time()

        if current_time - creation_time > self._expiration_seconds:
            del self._tokens[token]
            return False

        del self._tokens[token]
        return True
