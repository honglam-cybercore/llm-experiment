import bcrypt

def hash_password(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verify_password(password, stored):
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(stored, str):
        stored = stored.encode('utf-8')
    return bcrypt.checkpw(password, stored)
