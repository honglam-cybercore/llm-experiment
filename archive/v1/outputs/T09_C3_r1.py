import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


def generate_key() -> bytes:
    """Generate a cryptographically secure 256-bit key."""
    return os.urandom(32)


def encrypt(plaintext, key) -> bytes:
    """Encrypt plaintext using AES-256-GCM with a random nonce."""
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError("key must be 32 bytes")
    
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext = cipher.encrypt(nonce, plaintext_bytes, None)
    
    return nonce + ciphertext


def decrypt(ciphertext, key) -> str:
    """Decrypt ciphertext using AES-256-GCM."""
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError("key must be 32 bytes")
    
    if len(ciphertext) < 28:
        raise ValueError("ciphertext is malformed")
    
    nonce = ciphertext[:12]
    actual_ciphertext = ciphertext[12:]
    
    cipher = AESGCM(key)
    
    try:
        plaintext_bytes = cipher.decrypt(nonce, actual_ciphertext, None)
    except InvalidTag:
        raise ValueError("Decryption failed: invalid key or corrupted ciphertext")
    
    return plaintext_bytes.decode('utf-8')
