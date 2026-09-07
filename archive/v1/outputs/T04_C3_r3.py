import bcrypt


def hash_password(password) -> str:
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    if not password:
        raise ValueError("Password cannot be empty")
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, stored) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    if not password or not stored:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
    except (ValueError, TypeError):
        return False
