import hashlib
import hmac
import secrets

_SALT_LENGTH = 16
_KEY_LENGTH = 32
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_MAX_PASSWORD_LENGTH = 1_048_576
_MAX_STORED_LENGTH = 256


def _password_bytes(password):
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    if len(password) > _MAX_PASSWORD_LENGTH:
        raise ValueError("password is too long")
    return password.encode("utf-8")


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_LENGTH)
    digest = hashlib.scrypt(
        password_bytes,
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LENGTH,
    )
    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password, stored) -> bool:
    try:
        password_bytes = _password_bytes(password)
        if not isinstance(stored, str) or len(stored) > _MAX_STORED_LENGTH:
            return False

        parts = stored.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False

        n, r, p = (int(parts[1]), int(parts[2]), int(parts[3]))
        salt = bytes.fromhex(parts[4])
        expected = bytes.fromhex(parts[5])

        if (
            n != _SCRYPT_N
            or r != _SCRYPT_R
            or p != _SCRYPT_P
            or len(salt) != _SALT_LENGTH
            or len(expected) != _KEY_LENGTH
        ):
            return False

        actual = hashlib.scrypt(
            password_bytes,
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=_KEY_LENGTH,
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError, UnicodeError, OverflowError):
        return False