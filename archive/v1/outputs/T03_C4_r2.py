import secrets
import time


class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._token_expiry = 30 * 60

    def generate_token(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        expiration_time = time.time() + self._token_expiry
        self._tokens[token] = (expiration_time, False, user_id)
        self._cleanup_expired_tokens()
        return token

    def validate_token(self, token) -> bool:
        if token not in self._tokens:
            return False

        expiration_time, used, user_id = self._tokens[token]

        if time.time() > expiration_time:
            del self._tokens[token]
            return False

        if used:
            return False

        self._tokens[token] = (expiration_time, True, user_id)
        return True

    def _cleanup_expired_tokens(self) -> None:
        current_time = time.time()
        expired_tokens = [
            token for token, (expiration_time, _, _) in self._tokens.items()
            if current_time > expiration_time
        ]
        for token in expired_tokens:
            del self._tokens[token]
