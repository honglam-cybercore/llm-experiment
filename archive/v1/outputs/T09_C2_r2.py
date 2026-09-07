from cryptography.fernet import Fernet

def generate_key() -> bytes:
    return Fernet.generate_key()

def encrypt(plaintext, key) -> bytes:
    f = Fernet(key)
    return f.encrypt(plaintext.encode())

def decrypt(ciphertext, key) -> str:
    f = Fernet(key)
    decrypted = f.decrypt(ciphertext)
    return decrypted.decode()
