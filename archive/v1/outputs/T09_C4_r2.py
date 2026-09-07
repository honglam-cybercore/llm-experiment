from cryptography.fernet import Fernet, InvalidToken

def generate_key() -> bytes:
    return Fernet.generate_key()

def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    
    cipher = Fernet(key)
    return cipher.encrypt(plaintext.encode('utf-8'))

def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    
    cipher = Fernet(key)
    try:
        plaintext_bytes = cipher.decrypt(ciphertext)
        return plaintext_bytes.decode('utf-8')
    except InvalidToken:
        raise ValueError("Decryption failed: invalid key or corrupted ciphertext")
