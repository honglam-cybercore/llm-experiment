from secrets import token_bytes

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_VERSION = b"\x01"
_NONCE_SIZE = 12
_KEY_SIZE = 32
_TAG_SIZE = 16


def generate_key() -> bytes:
    return token_bytes(_KEY_SIZE)


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes) or len(key) != _KEY_SIZE:
        raise ValueError("invalid encryption key")

    nonce = token_bytes(_NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _VERSION)
    return _VERSION + nonce + ciphertext


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes) or len(key) != _KEY_SIZE:
        raise ValueError("invalid encryption key")
    if len(ciphertext) < len(_VERSION) + _NONCE_SIZE + _TAG_SIZE:
        raise ValueError("invalid ciphertext")
    if ciphertext[:1] != _VERSION:
        raise ValueError("invalid ciphertext")

    nonce = ciphertext[1:1 + _NONCE_SIZE]
    encrypted_data = ciphertext[1 + _NONCE_SIZE:]

    try:
        plaintext = AESGCM(key).decrypt(nonce, encrypted_data, _VERSION)
        return plaintext.decode("utf-8")
    except (InvalidTag, UnicodeDecodeError) as exc:
        raise ValueError("decryption failed") from exc