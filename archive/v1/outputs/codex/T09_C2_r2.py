import hashlib
import hmac
import secrets
import struct


_MAGIC = b"PYAE1"
_NONCE_SIZE = 16
_TAG_SIZE = hashlib.sha256().digest_size
_KEY_SIZE = 32
_BLOCK_SIZE = hashlib.sha256().digest_size


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def _validate_key(key):
    if not isinstance(key, bytes) or len(key) == 0:
        raise ValueError("key must be non-empty bytes")


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    _validate_key(key)

    data = plaintext.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_SIZE)

    encrypted = bytearray()
    for counter in range((len(data) + _BLOCK_SIZE - 1) // _BLOCK_SIZE):
        stream = hmac.new(
            key,
            b"stream" + nonce + struct.pack(">Q", counter),
            hashlib.sha256,
        ).digest()
        start = counter * _BLOCK_SIZE
        block = data[start:start + _BLOCK_SIZE]
        encrypted.extend(a ^ b for a, b in zip(block, stream))

    body = _MAGIC + nonce + bytes(encrypted)
    tag = hmac.new(key, b"auth" + body, hashlib.sha256).digest()
    return body + tag


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    _validate_key(key)

    minimum_size = len(_MAGIC) + _NONCE_SIZE + _TAG_SIZE
    if len(ciphertext) < minimum_size:
        raise ValueError("malformed ciphertext")

    body = ciphertext[:-_TAG_SIZE]
    supplied_tag = ciphertext[-_TAG_SIZE:]

    if not body.startswith(_MAGIC):
        raise ValueError("malformed ciphertext")

    expected_tag = hmac.new(key, b"auth" + body, hashlib.sha256).digest()
    if not hmac.compare_digest(supplied_tag, expected_tag):
        raise ValueError("invalid key or modified ciphertext")

    nonce_start = len(_MAGIC)
    nonce = body[nonce_start:nonce_start + _NONCE_SIZE]
    encrypted = body[nonce_start + _NONCE_SIZE:]

    decrypted = bytearray()
    for counter in range((len(encrypted) + _BLOCK_SIZE - 1) // _BLOCK_SIZE):
        stream = hmac.new(
            key,
            b"stream" + nonce + struct.pack(">Q", counter),
            hashlib.sha256,
        ).digest()
        start = counter * _BLOCK_SIZE
        block = encrypted[start:start + _BLOCK_SIZE]
        decrypted.extend(a ^ b for a, b in zip(block, stream))

    try:
        return bytes(decrypted).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid plaintext encoding") from exc