import hashlib
import hmac
import secrets
import struct


_KEY_SIZE = 32
_NONCE_SIZE = 12
_TAG_SIZE = 16
_HEADER = b"SC01"


def generate_key() -> bytes:
    return secrets.token_bytes(_KEY_SIZE)


def _validate_key(key):
    if not isinstance(key, bytes) or len(key) != _KEY_SIZE:
        raise ValueError("key must be exactly 32 bytes")


def _rotl32(value, shift):
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF


def _quarter_round(state, a, b, c, d):
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 7)


def _chacha20_block(key, counter, nonce):
    constants = b"expand 32-byte k"
    state = list(struct.unpack("<4I", constants))
    state += list(struct.unpack("<8I", key))
    state += [counter]
    state += list(struct.unpack("<3I", nonce))

    working = state[:]

    for _ in range(10):
        _quarter_round(working, 0, 4, 8, 12)
        _quarter_round(working, 1, 5, 9, 13)
        _quarter_round(working, 2, 6, 10, 14)
        _quarter_round(working, 3, 7, 11, 15)
        _quarter_round(working, 0, 5, 10, 15)
        _quarter_round(working, 1, 6, 11, 12)
        _quarter_round(working, 2, 7, 8, 13)
        _quarter_round(working, 3, 4, 9, 14)

    return struct.pack(
        "<16I",
        *[(working[i] + state[i]) & 0xFFFFFFFF for i in range(16)]
    )


def _chacha20_xor(data, key, nonce, counter=1):
    output = bytearray()
    for offset in range(0, len(data), 64):
        block = _chacha20_block(key, counter, nonce)
        chunk = data[offset:offset + 64]
        output.extend(a ^ b for a, b in zip(chunk, block))
        counter += 1
        if counter > 0xFFFFFFFF:
            raise ValueError("plaintext is too large")
    return bytes(output)


def _poly1305_mac(message, one_time_key):
    r_bytes = bytearray(one_time_key[:16])
    r_bytes[3] &= 15
    r_bytes[7] &= 15
    r_bytes[11] &= 15
    r_bytes[15] &= 15
    r_bytes[4] &= 252
    r_bytes[8] &= 252
    r_bytes[12] &= 252

    r = int.from_bytes(r_bytes, "little")
    s = int.from_bytes(one_time_key[16:], "little")
    modulus = (1 << 130) - 5
    accumulator = 0

    for offset in range(0, len(message), 16):
        block = message[offset:offset + 16]
        n = int.from_bytes(block + b"\x01", "little")
        accumulator = ((accumulator + n) * r) % modulus

    tag = (accumulator + s) & ((1 << 128) - 1)
    return tag.to_bytes(16, "little")


def _mac_data(header, ciphertext):
    padding = b"\x00" * ((16 - len(ciphertext) % 16) % 16)
    return (
        header
        + ciphertext
        + padding
        + struct.pack("<Q", len(header))
        + struct.pack("<Q", len(ciphertext))
    )


def encrypt(plaintext, key) -> bytes:
    _validate_key(key)
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    plaintext_bytes = plaintext.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_SIZE)
    header = _HEADER + nonce

    one_time_key = _chacha20_block(key, 0, nonce)[:32]
    ciphertext = _chacha20_xor(plaintext_bytes, key, nonce, 1)
    tag = _poly1305_mac(_mac_data(header, ciphertext), one_time_key)

    return header + ciphertext + tag


def decrypt(ciphertext, key) -> str:
    _validate_key(key)
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if len(ciphertext) < len(_HEADER) + _NONCE_SIZE + _TAG_SIZE:
        raise ValueError("malformed ciphertext")

    header = ciphertext[:len(_HEADER) + _NONCE_SIZE]
    if header[:len(_HEADER)] != _HEADER:
        raise ValueError("malformed ciphertext")

    nonce = header[len(_HEADER):]
    body = ciphertext[len(header):]
    encrypted_data = body[:-_TAG_SIZE]
    supplied_tag = body[-_TAG_SIZE:]

    one_time_key = _chacha20_block(key, 0, nonce)[:32]
    expected_tag = _poly1305_mac(
        _mac_data(header, encrypted_data),
        one_time_key,
    )

    if not hmac.compare_digest(supplied_tag, expected_tag):
        raise ValueError("authentication failed")

    plaintext_bytes = _chacha20_xor(encrypted_data, key, nonce, 1)
    try:
        return plaintext_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid plaintext encoding") from exc