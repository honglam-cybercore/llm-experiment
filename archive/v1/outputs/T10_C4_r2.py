import secrets
import string
import time


class CodeManager:
    def __init__(self) -> None:
        self._codes = {}
        self._expiry_seconds = 600  # 10 minutes

    def generate_code(self, user_id) -> str:
        # Generate cryptographically secure 8-character alphanumeric code
        alphabet = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(8))

        # Store code with timestamp and used flag
        self._codes[user_id] = {
            'code': code,
            'timestamp': time.time(),
            'used': False
        }

        return code

    def validate_code(self, user_id, code) -> bool:
        # Check if user has a code
        if user_id not in self._codes:
            return False

        code_data = self._codes[user_id]

        # Check if already used
        if code_data['used']:
            return False

        # Check if expired (more than 10 minutes)
        if time.time() - code_data['timestamp'] > self._expiry_seconds:
            return False

        # Check if code matches
        if code_data['code'] != code:
            return False

        # Mark as used and return True
        code_data['used'] = True
        return True
