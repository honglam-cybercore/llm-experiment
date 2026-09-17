import hashlib
import hmac
import secrets
import struct


_MAGIC = b"PYENC\x01"
_KEY_SIZE = 32
_NONCE_SIZE = 16
_TAG_SIZE = 32
_MAX_BLOCKS = (1 << 32) - 1


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def _validate_key(key) -> bytes:
    if not isinstance(key, bytes) or len(key) != _KEY_SIZE:
        raise ValueError("invalid encryption key")
    return key


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0

    while len(output) < length:
        if counter >= _MAX_BLOCKS:
            raise ValueError("plaintext is too large")
        output.extend(
            hmac.new(
                key,
                b"stream" + nonce + struct.pack(">Q", counter),
                hashlib.sha256,
            ).digest()
        )
        counter += 1

    return bytes(output[:length])


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    key = _validate_key(key)
    data = plaintext.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_SIZE)
    encrypted = bytes(
        value ^ mask
        for value, mask in zip(data, _keystream(key, nonce, len(data)))
    )

    body = _MAGIC + nonce + encrypted
    tag = hmac.new(key, b"auth" + body, hashlib.sha256).digest()
    return body + tag


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")

    key = _validate_key(key)

    minimum_length = len(_MAGIC) + _NONCE_SIZE + _TAG_SIZE
    if len(ciphertext) < minimum_length or not ciphertext.startswith(_MAGIC):
        raise ValueError("malformed or corrupted ciphertext")

    body = ciphertext[:-_TAG_SIZE]
    tag = ciphertext[-_TAG_SIZE:]
    expected_tag = hmac.new(key, b"auth" + body, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("incorrect key or corrupted ciphertext")

    nonce_start = len(_MAGIC)
    nonce_end = nonce_start + _NONCE_SIZE
    nonce = ciphertext[nonce_start:nonce_end]
    encrypted = ciphertext[nonce_end:-_TAG_SIZE]

    data = bytes(
        value ^ mask
        for value, mask in zip(encrypted, _keystream(key, nonce, len(encrypted)))
    )

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("malformed ciphertext") from exc