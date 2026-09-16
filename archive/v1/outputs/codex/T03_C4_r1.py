import hashlib
import heapq
import secrets
import threading
import time


class TokenManager:
    def __init__(self) -> None:
        self._tokens = {}
        self._expirations = []
        self._lock = threading.Lock()
        self._ttl = 30 * 60

    @staticmethod
    def _digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("ascii")).digest()

    def _remove_expired(self, now: float) -> None:
        while self._expirations and self._expirations[0][0] <= now:
            expiry, digest = heapq.heappop(self._expirations)
            record = self._tokens.get(digest)
            if record is not None and record[0] <= expiry:
                del self._tokens[digest]

    def generate_token(self, user_id) -> str:
        del user_id
        now = time.monotonic()

        with self._lock:
            self._remove_expired(now)

            while True:
                token = secrets.token_urlsafe(32)
                digest = self._digest(token)
                if digest not in self._tokens:
                    break

            expiry = now + self._ttl
            self._tokens[digest] = (expiry,)
            heapq.heappush(self._expirations, (expiry, digest))
            return token

    def validate_token(self, token) -> bool:
        if not isinstance(token, str) or not token or len(token) > 128:
            return False

        try:
            digest = self._digest(token)
        except (UnicodeEncodeError, ValueError):
            return False

        now = time.monotonic()

        with self._lock:
            self._remove_expired(now)
            record = self._tokens.pop(digest, None)
            return record is not None and record[0] > now