import hashlib
import os
import base64

def hash_password(password) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = os.urandom(32)
    hash_obj = hashlib.scrypt(
        password,
        salt=salt,
        n=16384,
        r=8,
        p=1
    )
    return base64.b64encode(salt + hash_obj).decode('utf-8')

def verify_password(password, stored) -> bool:
    try:
        if isinstance(password, str):
            password = password.encode('utf-8')
        data = base64.b64decode(stored.encode('utf-8') if isinstance(stored, str) else stored)
        salt = data[:32]
        hash_obj = hashlib.scrypt(
            password,
            salt=salt,
            n=16384,
            r=8,
            p=1
        )
        return data[32:] == hash_obj
    except Exception:
        return False
