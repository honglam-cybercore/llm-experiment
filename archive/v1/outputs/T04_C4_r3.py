import bcrypt

def hash_password(password) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    elif not isinstance(password, bytes):
        raise TypeError("Password must be a string or bytes")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verify_password(password, stored) -> bool:
    try:
        if isinstance(password, str):
            password = password.encode('utf-8')
        elif not isinstance(password, bytes):
            return False
        if isinstance(stored, str):
            stored = stored.encode('utf-8')
        elif not isinstance(stored, bytes):
            return False
        return bcrypt.checkpw(password, stored)
    except Exception:
        return False
