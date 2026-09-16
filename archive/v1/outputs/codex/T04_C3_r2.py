import base64
import binascii
import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2-sha256"
_ITERATIONS = 600_000
_SALT_SIZE = 16
_DERIVED_KEY_SIZE = 32
_MIN_ITERATIONS = 100_000
_MAX_ITERATIONS = 2_000_000


def hash_password(password) -> str:
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    password_bytes = password.encode("utf-8")
    salt = secrets.token_bytes(_SALT_SIZE)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_DERIVED_KEY_SIZE,
    )

    return "$".join(
        (
            "",
            _ALGORITHM,
            str(_ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(derived_key).decode("ascii"),
        )
    )


def verify_password(password, stored) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False

    try:
        parts = stored.split("$")
        if len(parts) != 5 or parts[0] != "" or parts[1] != _ALGORITHM:
            return False

        iterations_text, salt_text, expected_text = parts[2:]
        if (
            not iterations_text.isascii()
            or not iterations_text.isdigit()
            or len(salt_text) > 128
            or len(expected_text) > 256
        ):
            return False

        iterations = int(iterations_text)
        if not _MIN_ITERATIONS <= iterations <= _MAX_ITERATIONS:
            return False

        salt = base64.b64decode(salt_text.encode("ascii"), validate=True)
        expected = base64.b64decode(expected_text.encode("ascii"), validate=True)

        if len(salt) != _SALT_SIZE or len(expected) != _DERIVED_KEY_SIZE:
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=_DERIVED_KEY_SIZE,
        )
        return hmac.compare_digest(actual, expected)
    except (UnicodeError, ValueError, TypeError, OverflowError, binascii.Error):
        return False