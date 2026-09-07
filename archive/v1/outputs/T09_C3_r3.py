from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def generate_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)

def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    if len(key) not in [16, 24, 32]:
        raise ValueError("key must be 16, 24, or 32 bytes")
    
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext = cipher.encrypt(nonce, plaintext_bytes, None)
    
    return nonce + ciphertext

def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    if len(key) not in [16, 24, 32]:
        raise ValueError("key must be 16, 24, or 32 bytes")
    if len(ciphertext) < 12:
        raise ValueError("ciphertext is too short")
    
    nonce = ciphertext[:12]
    actual_ciphertext = ciphertext[12:]
    
    cipher = AESGCM(key)
    plaintext_bytes = cipher.decrypt(nonce, actual_ciphertext, None)
    
    return plaintext_bytes.decode('utf-8')
