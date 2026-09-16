import base64
import hashlib
import hmac
import os

_ITERATIONS = 600_000
_SALT_SIZE = 16
_KEY_SIZE = 32


def hash_password(password) -> str:
    if not isinstance(password, (str, bytes)):
        raise TypeError("password must be a string or bytes")

    password_bytes = password.encode("utf-8") if isinstance(password, str) else password
    salt = os.urandom(_SALT_SIZE)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_KEY_SIZE,
    )

    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_key = base64.b64encode(derived_key).decode("ascii")
    return f"$pbkdf2-sha256${_ITERATIONS}${encoded_salt}${encoded_key}"


def verify_password(password, stored) -> bool:
    if not isinstance(password, (str, bytes)) or not isinstance(stored, str):
        return False

    try:
        parts = stored.split("$")
        if len(parts) != 5 or parts[0] != "" or parts[1] != "pbkdf2-sha256":
            return False

        iterations = int(parts[2])
        if iterations != _ITERATIONS:
            return False

        salt = base64.b64decode(parts[3], validate=True)
        expected_key = base64.b64decode(parts[4], validate=True)

        if len(salt) != _SALT_SIZE or len(expected_key) != _KEY_SIZE:
            return False

        password_bytes = password.encode("utf-8") if isinstance(password, str) else password
        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt,
            iterations,
            dklen=_KEY_SIZE,
        )
        return hmac.compare_digest(actual_key, expected_key)
    except (ValueError, TypeError):
        return False