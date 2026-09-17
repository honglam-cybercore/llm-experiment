import hashlib
import hmac
import secrets
import struct

_MAGIC = b"AE1"
_NONCE_SIZE = 16
_TAG_SIZE = 32
_KEY_SIZE = 32


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0

    while len(output) < length:
        output.extend(
            hmac.new(
                key,
                nonce + struct.pack(">Q", counter),
                hashlib.sha256,
            ).digest()
        )
        counter += 1

    return bytes(output[:length])


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a str")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")

    data = plaintext.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_SIZE)
    encrypted = bytes(
        value ^ mask
        for value, mask in zip(data, _keystream(key, nonce, len(data)))
    )

    body = _MAGIC + nonce + encrypted
    tag = hmac.new(key, body, hashlib.sha256).digest()
    return body + tag


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")
    if len(ciphertext) < len(_MAGIC) + _NONCE_SIZE + _TAG_SIZE:
        raise ValueError("malformed ciphertext")
    if not ciphertext.startswith(_MAGIC):
        raise ValueError("malformed ciphertext")

    body = ciphertext[:-_TAG_SIZE]
    received_tag = ciphertext[-_TAG_SIZE:]
    expected_tag = hmac.new(key, body, hashlib.sha256).digest()

    if not hmac.compare_digest(received_tag, expected_tag):
        raise ValueError("authentication failed")

    nonce = body[len(_MAGIC):len(_MAGIC) + _NONCE_SIZE]
    encrypted = body[len(_MAGIC) + _NONCE_SIZE:]
    data = bytes(
        value ^ mask
        for value, mask in zip(encrypted, _keystream(key, nonce, len(encrypted)))
    )

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("malformed plaintext") from exc