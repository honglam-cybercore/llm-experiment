import bcrypt

def hash_password(password) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(password, stored) -> bool:
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(stored, str):
        stored = stored.encode('utf-8')
    return bcrypt.checkpw(password, stored)
