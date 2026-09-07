import secrets
import string
import time
from typing import Dict, Tuple

class CodeManager:
    def __init__(self) -> None:
        self._codes: Dict[str, Tuple[str, float, bool]] = {}
        self._expiry_seconds = 10 * 60

    def generate_code(self, user_id) -> str:
        if not isinstance(user_id, (str, int)):
            raise ValueError("user_id must be string or integer")
        
        user_id_str = str(user_id)
        if not user_id_str:
            raise ValueError("user_id cannot be empty")
        
        alphabet = string.ascii_letters + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            if code not in self._codes:
                break
        
        self._codes[code] = (user_id_str, time.time(), False)
        return code

    def validate_code(self, user_id, code) -> bool:
        if not isinstance(user_id, (str, int)) or not isinstance(code, str):
            return False
        
        user_id_str = str(user_id)
        
        if not user_id_str or not code:
            return False
        
        if code not in self._codes:
            return False
        
        stored_user_id, timestamp, used = self._codes[code]
        
        if stored_user_id != user_id_str:
            return False
        
        if used:
            return False
        
        if time.time() - timestamp > self._expiry_seconds:
            return False
        
        self._codes[code] = (stored_user_id, timestamp, True)
        
        return True
