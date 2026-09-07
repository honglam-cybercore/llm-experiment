import secrets
import string
import time
from typing import Dict, Tuple

class CodeManager:
    CODE_LENGTH = 8
    EXPIRY_TIME = 10 * 60
    
    def __init__(self) -> None:
        self._codes: Dict[str, Dict[str, Tuple[float, bool]]] = {}
    
    def generate_code(self, user_id) -> str:
        alphabet = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(self.CODE_LENGTH))
        
        if user_id not in self._codes:
            self._codes[user_id] = {}
        
        self._codes[user_id][code] = (time.time(), False)
        return code
    
    def validate_code(self, user_id, code) -> bool:
        if user_id not in self._codes or code not in self._codes[user_id]:
            return False
        
        timestamp, used = self._codes[user_id][code]
        
        if used:
            return False
        
        if time.time() - timestamp > self.EXPIRY_TIME:
            return False
        
        self._codes[user_id][code] = (timestamp, True)
        return True
