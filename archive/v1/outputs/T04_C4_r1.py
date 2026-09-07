try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

import hashlib
import secrets
import base64

def hash_password(password) -> str:
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        salt = secrets.token_bytes(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return 'pbkdf2$' + base64.b64encode(salt + key).decode('ascii')

def verify_password(password, stored) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    
    try:
        if stored.startswith('pbkdf2$'):
            encoded = stored[7:]
            decoded = base64.b64decode(encoded)
            if len(decoded) < 32:
                return False
            salt = decoded[:16]
            stored_key = decoded[16:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return secrets.compare_digest(key, stored_key)
        elif HAS_BCRYPT:
            return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
        else:
            return False
    except Exception:
        return False
