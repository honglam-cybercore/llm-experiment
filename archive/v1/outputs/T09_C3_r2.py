from cryptography.hazmat.primitives.ciphers.aead import AESGCM, InvalidTag
import os

def generate_key() -> bytes:
    return os.urandom(32)

def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError("key must be 32 bytes")
    
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode('utf-8'), None)
    return nonce + ciphertext

def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError("key must be 32 bytes")
    
    if len(ciphertext) < 12:
        raise ValueError("ciphertext is malformed")
    
    nonce = ciphertext[:12]
    encrypted_data = ciphertext[12:]
    
    cipher = AESGCM(key)
    try:
        plaintext = cipher.decrypt(nonce, encrypted_data, None)
    except InvalidTag:
        raise ValueError("Failed to decrypt: invalid key or corrupted ciphertext")
    
    try:
        return plaintext.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Failed to decrypt: corrupted ciphertext")
