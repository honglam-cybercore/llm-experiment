import bcrypt

def hash_password(password) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, stored) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
