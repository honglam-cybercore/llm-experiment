from cryptography.fernet import Fernet

def generate_key() -> bytes:
    """Generate a new encryption key."""
    return Fernet.generate_key()

def encrypt(plaintext, key) -> bytes:
    """Encrypt plaintext with the given key."""
    cipher = Fernet(key)
    return cipher.encrypt(plaintext.encode())

def decrypt(ciphertext, key) -> str:
    """Decrypt ciphertext with the given key."""
    cipher = Fernet(key)
    return cipher.decrypt(ciphertext).decode()
