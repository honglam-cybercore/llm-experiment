import secrets
import time
from typing import Dict, Tuple


class TokenManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, Tuple[str, float, bool]] = {}
        self._expiration_seconds = 30 * 60

    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        expiration_time = time.time() + self._expiration_seconds
        self._tokens[token] = (str(user_id), expiration_time, False)
        return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token:
            return False

        if token not in self._tokens:
            return False

        user_id_str, expiration_time, used = self._tokens[token]

        if time.time() > expiration_time:
            del self._tokens[token]
            return False

        if used:
            return False

        self._tokens[token] = (user_id_str, expiration_time, True)
        return True
