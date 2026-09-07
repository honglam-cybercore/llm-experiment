import bcrypt

def hash_password(password) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    elif not isinstance(password, bytes):
        password = str(password).encode('utf-8')
    
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verify_password(password, stored) -> bool:
    if not isinstance(password, (str, bytes)):
        return False
    if not isinstance(stored, str):
        return False
    
    try:
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.checkpw(password, stored.encode('utf-8'))
    except (ValueError, TypeError):
        return False
