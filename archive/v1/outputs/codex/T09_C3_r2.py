from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_KEY_SIZE = 32
_NONCE_SIZE = 12


def generate_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    if len(key) != _KEY_SIZE:
        raise ValueError("key must be 32 bytes")

    nonce = AESGCM.generate_key(bit_length=96)
    return nonce + AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    if len(key) != _KEY_SIZE:
        raise ValueError("key must be 32 bytes")
    if len(ciphertext) <= _NONCE_SIZE + 16:
        raise ValueError("malformed ciphertext")

    nonce = ciphertext[:_NONCE_SIZE]
    payload = ciphertext[_NONCE_SIZE:]

    try:
        plaintext = AESGCM(key).decrypt(nonce, payload, None)
        return plaintext.decode("utf-8")
    except (InvalidTag, UnicodeDecodeError) as exc:
        raise ValueError("invalid ciphertext or key") from exc