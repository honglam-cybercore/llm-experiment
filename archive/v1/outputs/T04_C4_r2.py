import bcrypt

def hash_password(password) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def verify_password(password, stored) -> bool:
    try:
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(stored, str):
            stored = stored.encode('utf-8')
        return bcrypt.checkpw(password, stored)
    except (ValueError, TypeError):
        return False
