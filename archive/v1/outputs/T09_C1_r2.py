from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def generate_key() -> bytes:
    return os.urandom(32)

def encrypt(plaintext, key) -> bytes:
    plaintext_bytes = plaintext.encode('utf-8')
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext_bytes, None)
    return nonce + ciphertext

def decrypt(ciphertext, key) -> str:
    nonce = ciphertext[:12]
    encrypted_data = ciphertext[12:]
    cipher = AESGCM(key)
    plaintext_bytes = cipher.decrypt(nonce, encrypted_data, None)
    return plaintext_bytes.decode('utf-8')
