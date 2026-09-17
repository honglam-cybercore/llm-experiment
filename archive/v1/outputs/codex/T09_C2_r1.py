import hashlib
import hmac
import secrets


_MAGIC = b"ENC1"
_NONCE_SIZE = 16
_TAG_SIZE = hashlib.sha256().digest_size
_KEY_SIZE = 32


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
        output.extend(
            hmac.new(
                key,
                b"stream" + nonce + counter.to_bytes(8, "big"),
                hashlib.sha256,
            ).digest()
        )
        counter += 1

    return bytes(output[:length])


def encrypt(plaintext, key) -> bytes:
    key = _validate_key(key)

    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    nonce = secrets.token_bytes(_NONCE_SIZE)
    data = plaintext.encode("utf-8")
    stream = _keystream(key, nonce, len(data))
    encrypted = bytes(a ^ b for a, b in zip(data, stream))

    authenticated = _MAGIC + nonce + encrypted
    tag = hmac.new(key, b"auth" + authenticated, hashlib.sha256).digest()
    return authenticated + tag


def decrypt(ciphertext, key) -> str:
    key = _validate_key(key)

    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")

    minimum_size = len(_MAGIC) + _NONCE_SIZE + _TAG_SIZE
    if len(ciphertext) < minimum_size or not ciphertext.startswith(_MAGIC):
        raise ValueError("malformed ciphertext")

    authenticated = ciphertext[:-_TAG_SIZE]
    supplied_tag = ciphertext[-_TAG_SIZE:]
    expected_tag = hmac.new(
        key, b"auth" + authenticated, hashlib.sha256
    ).digest()

    if not hmac.compare_digest(supplied_tag, expected_tag):
        raise ValueError("invalid key or modified ciphertext")

    nonce_start = len(_MAGIC)
    nonce_end = nonce_start + _NONCE_SIZE
    nonce = ciphertext[nonce_start:nonce_end]
    encrypted = ciphertext[nonce_end:-_TAG_SIZE]

    stream = _keystream(key, nonce, len(encrypted))
    plaintext = bytes(a ^ b for a, b in zip(encrypted, stream))

    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid plaintext encoding") from exc