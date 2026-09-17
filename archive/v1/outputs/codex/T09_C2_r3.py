import hashlib
import hmac
import secrets
import struct


_MAGIC = b"ENC1"
_NONCE_SIZE = 16
_TAG_SIZE = 32
_KEY_SIZE = 32


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0

    while len(output) < length:
        block = hmac.new(
            key,
            b"stream" + nonce + struct.pack(">Q", counter),
            hashlib.sha256,
        ).digest()
        output.extend(block)
        counter += 1

    return bytes(output[:length])


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, bytes) or not key:
        raise TypeError("key must be non-empty bytes")

    plaintext_bytes = plaintext.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_SIZE)
    ciphertext = bytes(
        value ^ mask
        for value, mask in zip(
            plaintext_bytes,
            _keystream(key, nonce, len(plaintext_bytes)),
        )
    )

    body = _MAGIC + nonce + ciphertext
    tag = hmac.new(key, body, hashlib.sha256).digest()
    return body + tag


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes) or not key:
        raise TypeError("key must be non-empty bytes")

    minimum_size = len(_MAGIC) + _NONCE_SIZE + _TAG_SIZE
    if len(ciphertext) < minimum_size:
        raise ValueError("malformed ciphertext")
    if not ciphertext.startswith(_MAGIC):
        raise ValueError("malformed ciphertext")

    body = ciphertext[:-_TAG_SIZE]
    tag = ciphertext[-_TAG_SIZE:]
    expected_tag = hmac.new(key, body, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("invalid key or modified ciphertext")

    nonce_start = len(_MAGIC)
    nonce_end = nonce_start + _NONCE_SIZE
    nonce = ciphertext[nonce_start:nonce_end]
    encrypted = ciphertext[nonce_end:-_TAG_SIZE]

    plaintext_bytes = bytes(
        value ^ mask
        for value, mask in zip(
            encrypted,
            _keystream(key, nonce, len(encrypted)),
        )
    )

    try:
        return plaintext_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("malformed plaintext") from exc