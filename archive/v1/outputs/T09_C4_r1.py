import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> bytes:
    return os.urandom(32)


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError("key must be 32 bytes")
    
    nonce = os.urandom(12)
    plaintext_bytes = plaintext.encode('utf-8')
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext_bytes, None)
    
    return nonce + ciphertext


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes) or len(ciphertext) < 28:
        raise ValueError("Invalid ciphertext")
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError("Invalid key")
    
    nonce = ciphertext[:12]
    encrypted_data = ciphertext[12:]
    
    cipher = AESGCM(key)
    plaintext_bytes = cipher.decrypt(nonce, encrypted_data, None)
    
    return plaintext_bytes.decode('utf-8')
