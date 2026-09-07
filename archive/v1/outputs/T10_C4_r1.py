import secrets
import time
import hashlib
import string
from typing import Dict, Tuple

class CodeManager:
    def __init__(self) -> None:
        self._codes: Dict[str, Tuple[str, float, bool]] = {}
        self._expiry_seconds = 600
        self._alphabet = string.ascii_letters + string.digits
    
    def generate_code(self, user_id) -> str:
        user_id_str = str(user_id)
        code = ''.join(secrets.choice(self._alphabet) for _ in range(8))
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        self._codes[user_id_str] = (code_hash, time.time(), False)
        return code
    
    def validate_code(self, user_id, code) -> bool:
        try:
            if not isinstance(code, str):
                return False
            
            user_id_str = str(user_id)
            
            if user_id_str not in self._codes:
                return False
            
            code_hash, timestamp, used = self._codes[user_id_str]
            
            if used:
                return False
            
            if time.time() - timestamp > self._expiry_seconds:
                return False
            
            provided_hash = hashlib.sha256(code.encode()).hexdigest()
            if not secrets.compare_digest(provided_hash, code_hash):
                return False
            
            self._codes[user_id_str] = (code_hash, timestamp, True)
            
            return True
        except Exception:
            return False
