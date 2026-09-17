import hashlib
import hmac
import secrets
import struct

_MAGIC = b"ETX1"
_NONCE_SIZE = 16
_TAG_SIZE = 32
_KEY_SIZE = 32
_BLOCK_SIZE = hashlib.sha256().digest_size


def _normalize_key(key):
    if not isinstance(key, (bytes, bytearray, memoryview)):
        raise TypeError("key must be bytes-like")
    key = bytes(key)
    if len(key) != _KEY_SIZE:
        raise ValueError("invalid key")
    return key


def _derive_key(key, purpose):
    return hmac.new(key, purpose, hashlib.sha256).digest()


def _crypt(data, key, nonce):
    output = bytearray()
    enc_key = _derive_key(key, b"encryption")
    for counter, offset in enumerate(range(0, len(data), _BLOCK_SIZE)):
        stream = hmac.new(
            enc_key,
            nonce + struct.pack(">Q", counter),
            hashlib.sha256,
        ).digest()
        block = data[offset:offset + _BLOCK_SIZE]
        output.extend(a ^ b for a, b in zip(block, stream))
    return bytes(output)


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    key = _normalize_key(key)
    nonce = secrets.token_bytes(_NONCE_SIZE)
    data = plaintext.encode("utf-8")
    ciphertext = _crypt(data, key, nonce)

    authenticated = _MAGIC + nonce + ciphertext
    mac_key = _derive_key(key, b"authentication")
    tag = hmac.new(mac_key, authenticated, hashlib.sha256).digest()

    return authenticated + tag


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, (bytes, bytearray, memoryview)):
        raise TypeError("ciphertext must be bytes-like")

    key = _normalize_key(key)
    ciphertext = bytes(ciphertext)

    minimum_size = len(_MAGIC) + _NONCE_SIZE + _TAG_SIZE
    if len(ciphertext) < minimum_size:
        raise ValueError("malformed ciphertext")

    if ciphertext[:len(_MAGIC)] != _MAGIC:
        raise ValueError("malformed ciphertext")

    nonce_start = len(_MAGIC)
    nonce_end = nonce_start + _NONCE_SIZE
    nonce = ciphertext[nonce_start:nonce_end]
    tag = ciphertext[-_TAG_SIZE:]
    body = ciphertext[:-_TAG_SIZE]

    mac_key = _derive_key(key, b"authentication")
    expected_tag = hmac.new(mac_key, body, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("invalid key or modified ciphertext")

    plaintext = _crypt(body[nonce_end:], key, nonce)

    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("malformed ciphertext") from exc