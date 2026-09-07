import bcrypt

def hash_password(password) -> str:
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    if not password:
        raise ValueError("password cannot be empty")
    
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(password, stored) -> bool:
    if not isinstance(password, str):
        return False
    if not isinstance(stored, str):
        return False
    
    try:
        password_bytes = password.encode('utf-8')
        stored_bytes = stored.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_bytes)
    except (ValueError, TypeError):
        return False
