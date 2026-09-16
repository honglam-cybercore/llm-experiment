import base64
import hashlib
import hmac
import secrets


_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_LENGTH = 16
_DERIVED_KEY_LENGTH = 32
_MAX_PASSWORD_BYTES = 1 << 20
_MAX_STORED_LENGTH = 512


def _password_bytes(password):
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    value = password.encode("utf-8")
    if len(value) > _MAX_PASSWORD_BYTES:
        raise ValueError("password is too long")
    return value


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_LENGTH)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_DERIVED_KEY_LENGTH,
    )
    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_key = base64.b64encode(derived_key).decode("ascii")
    return f"{_ALGORITHM}${_ITERATIONS}${encoded_salt}${encoded_key}"


def verify_password(password, stored) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    if len(stored) > _MAX_STORED_LENGTH:
        return False

    try:
        password_bytes = _password_bytes(password)
        algorithm, iteration_text, encoded_salt, encoded_key = stored.split("$")
        if algorithm != _ALGORITHM:
            return False

        iterations = int(iteration_text)
        if not 100_000 <= iterations <= 1_000_000:
            return False

        salt = base64.b64decode(encoded_salt, validate=True)
        expected_key = base64.b64decode(encoded_key, validate=True)
        if len(salt) != _SALT_LENGTH or len(expected_key) != _DERIVED_KEY_LENGTH:
            return False

        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt,
            iterations,
            dklen=_DERIVED_KEY_LENGTH,
        )
        return hmac.compare_digest(actual_key, expected_key)
    except (TypeError, ValueError, UnicodeError):
        return False