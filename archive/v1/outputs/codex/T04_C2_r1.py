import base64
import hashlib
import hmac
import secrets


_ITERATIONS = 600_000
_SALT_SIZE = 16
_KEY_SIZE = 32
_ALGORITHM = "pbkdf2_sha256"


def _password_bytes(password):
    if isinstance(password, str):
        return password.encode("utf-8")
    if isinstance(password, bytes):
        return password
    raise TypeError("password must be a string or bytes")


def _encode(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_SIZE)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_KEY_SIZE,
    )
    return f"${_ALGORITHM}${_ITERATIONS}${_encode(salt)}${_encode(digest)}"


def verify_password(password, stored) -> bool:
    try:
        password_bytes = _password_bytes(password)
        if not isinstance(stored, str):
            return False

        parts = stored.split("$")
        if len(parts) != 5 or parts[0] != "" or parts[1] != _ALGORITHM:
            return False

        iterations = int(parts[2])
        salt = _decode(parts[3])
        expected = _decode(parts[4])

        if iterations <= 0 or not salt or not expected:
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt,
            iterations,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError, UnicodeError):
        return False