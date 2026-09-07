from cryptography.fernet import Fernet

def generate_key() -> bytes:
    return Fernet.generate_key()

def encrypt(plaintext, key) -> bytes:
    cipher = Fernet(key)
    return cipher.encrypt(plaintext.encode())

def decrypt(ciphertext, key) -> str:
    cipher = Fernet(key)
    plaintext_bytes = cipher.decrypt(ciphertext)
    return plaintext_bytes.decode()
