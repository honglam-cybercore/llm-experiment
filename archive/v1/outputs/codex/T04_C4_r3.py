import base64
import hashlib
import hmac
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32
_SALT_BYTES = 16
_MAX_PASSWORD_BYTES = 1024 * 1024
_MAX_STORED_LENGTH = 256


def _password_bytes(password):
    if isinstance(password, str):
        value = password.encode("utf-8")
    elif isinstance(password, bytes):
        value = password
    else:
        raise TypeError("password must be str or bytes")

    if len(value) > _MAX_PASSWORD_BYTES:
        raise ValueError("password is too long")
    return value


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password_bytes,
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_DKLEN,
        maxmem=64 * 1024 * 1024,
    )
    return (
        "scrypt$v=1$ln=14$r=8$p=1$"
        f"{base64.urlsafe_b64encode(salt).decode('ascii')}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii')}"
    )


def verify_password(password, stored) -> bool:
    try:
        password_bytes = _password_bytes(password)
        if not isinstance(stored, str) or len(stored) > _MAX_STORED_LENGTH:
            return False

        parts = stored.split("$")
        if len(parts) != 7 or parts[:5] != [
            "scrypt",
            "v=1",
            "ln=14",
            "r=8",
            "p=1",
        ]:
            return False

        salt = base64.urlsafe_b64decode(parts[5].encode("ascii"))
        expected = base64.urlsafe_b64decode(parts[6].encode("ascii"))

        if len(salt) != _SALT_BYTES or len(expected) != _DKLEN:
            return False

        actual = hashlib.scrypt(
            password_bytes,
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_DKLEN,
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError, UnicodeError, binascii.Error):
        return False