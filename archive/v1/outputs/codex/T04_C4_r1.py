import base64
import hashlib
import hmac
import secrets


_SALT_BYTES = 16
_HASH_BYTES = 32
_SCRYPT_N = 1 << 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_MAX_PASSWORD_BYTES = 4096
_MAX_STORED_LENGTH = 512


def _password_bytes(password):
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    value = password.encode("utf-8")
    if not value or len(value) > _MAX_PASSWORD_BYTES:
        raise ValueError("password has an invalid length")
    return value


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.scrypt(
        password_bytes,
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_HASH_BYTES,
        maxmem=64 * 1024 * 1024,
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return f"$scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encode(salt)}${encode(derived)}"


def verify_password(password, stored) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    if len(stored) > _MAX_STORED_LENGTH:
        return False

    parts = stored.split("$")
    if len(parts) != 7 or parts[1] != "scrypt":
        return False

    try:
        n, r, p = (int(parts[i]) for i in (2, 3, 4))
        if n != _SCRYPT_N or r != _SCRYPT_R or p != _SCRYPT_P:
            return False

        def decode(value):
            if not value or len(value) % 4 == 1:
                raise ValueError
            return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

        salt = decode(parts[5])
        expected = decode(parts[6])
        password_bytes = _password_bytes(password)

        if len(salt) != _SALT_BYTES or len(expected) != _HASH_BYTES:
            return False

        actual = hashlib.scrypt(
            password_bytes,
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError, OverflowError):
        return False