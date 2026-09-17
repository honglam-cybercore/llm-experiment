import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_MAGIC = b"ENC1"
_KEY_SIZE = 32
_NONCE_SIZE = 12


def _validate_key(key):
    if not isinstance(key, bytes) or len(key) != _KEY_SIZE:
        raise ValueError("invalid encryption key")


def generate_key() -> bytes:
    return os.urandom(_KEY_SIZE)


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    _validate_key(key)

    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _MAGIC)
    return _MAGIC + nonce + ciphertext


def decrypt(ciphertext, key) -> str:
    _validate_key(key)

    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if len(ciphertext) < len(_MAGIC) + _NONCE_SIZE + 16:
        raise ValueError("decryption failed")
    if not ciphertext.startswith(_MAGIC):
        raise ValueError("decryption failed")

    nonce_start = len(_MAGIC)
    nonce_end = nonce_start + _NONCE_SIZE
    nonce = ciphertext[nonce_start:nonce_end]
    encrypted_data = ciphertext[nonce_end:]

    try:
        plaintext = AESGCM(key).decrypt(nonce, encrypted_data, _MAGIC)
        return plaintext.decode("utf-8")
    except (InvalidTag, ValueError, UnicodeDecodeError):
        raise ValueError("decryption failed") from None