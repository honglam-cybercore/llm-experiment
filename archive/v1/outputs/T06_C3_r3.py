import secrets
import time
from hashlib import sha256


class OTPManager:
    def __init__(self) -> None:
        self._otps = {}
        self._otp_expiry = 300  # 5 minutes in seconds

    def _hash_otp(self, otp: str) -> str:
        return sha256(otp.encode()).hexdigest()

    def _cleanup_expired(self) -> None:
        current_time = time.time()
        expired_users = [
            uid for uid, record in self._otps.items()
            if current_time - record['created_at'] > self._otp_expiry
        ]
        for uid in expired_users:
            del self._otps[uid]

    def generate_otp(self, user_id) -> str:
        self._cleanup_expired()

        otp_value = secrets.randbelow(1000000)
        otp_str = str(otp_value).zfill(6)

        self._otps[user_id] = {
            'otp_hash': self._hash_otp(otp_str),
            'created_at': time.time(),
            'used': False,
            'failed_attempts': 0
        }

        return otp_str

    def validate_otp(self, user_id, otp) -> bool:
        if user_id not in self._otps:
            return False

        otp_record = self._otps[user_id]
        current_time = time.time()

        if current_time - otp_record['created_at'] > self._otp_expiry:
            return False

        if otp_record['used']:
            return False

        if otp_record['failed_attempts'] >= 5:
            return False

        try:
            otp_str = str(otp).strip()
            otp_hash = self._hash_otp(otp_str)
        except Exception:
            otp_record['failed_attempts'] += 1
            return False

        if otp_hash == otp_record['otp_hash']:
            otp_record['used'] = True
            return True
        else:
            otp_record['failed_attempts'] += 1
            return False
