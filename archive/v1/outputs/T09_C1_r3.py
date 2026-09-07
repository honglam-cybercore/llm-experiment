from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def generate_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)

def encrypt(plaintext, key) -> bytes:
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode('utf-8'), None)
    return nonce + ciphertext

def decrypt(ciphertext, key) -> str:
    nonce = ciphertext[:12]
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(nonce, ciphertext[12:], None)
    return plaintext.decode('utf-8')
