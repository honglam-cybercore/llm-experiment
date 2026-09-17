from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets


_HEADER = b"TXE1"
_KEY_SIZE = 32
_NONCE_SIZE = 12
_TAG_SIZE = 16


def _validate_key(key):
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    if len(key) != _KEY_SIZE:
        raise ValueError("key must be 32 bytes")


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be str")
    _validate_key(key)

    nonce = secrets.token_bytes(_NONCE_SIZE)
    encrypted = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _HEADER)
    return _HEADER + nonce + encrypted


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    _validate_key(key)

    minimum_size = len(_HEADER) + _NONCE_SIZE + _TAG_SIZE
    if len(ciphertext) < minimum_size or ciphertext[:len(_HEADER)] != _HEADER:
        raise ValueError("malformed ciphertext")

    nonce_start = len(_HEADER)
    nonce_end = nonce_start + _NONCE_SIZE
    nonce = ciphertext[nonce_start:nonce_end]
    encrypted = ciphertext[nonce_end:]

    try:
        plaintext = AESGCM(key).decrypt(nonce, encrypted, _HEADER)
        return plaintext.decode("utf-8")
    except (InvalidTag, UnicodeDecodeError):
        raise ValueError("invalid ciphertext or key") from None