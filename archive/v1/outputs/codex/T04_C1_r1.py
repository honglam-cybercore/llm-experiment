import base64
import hashlib
import hmac
import secrets


_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16
_DIGEST_BYTES = 32


def _password_bytes(password):
    if isinstance(password, str):
        return password.encode("utf-8")
    if isinstance(password, bytes):
        return password
    raise TypeError("password must be a string or bytes")


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_DIGEST_BYTES,
    )
    return "$".join(
        (
            _ALGORITHM,
            str(_ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password, stored) -> bool:
    if not isinstance(stored, str):
        return False

    try:
        algorithm, iterations_text, salt_text, digest_text = stored.split("$")
        if algorithm != _ALGORITHM:
            return False

        iterations = int(iterations_text)
        if iterations <= 0:
            return False

        salt = base64.b64decode(salt_text.encode("ascii"), validate=True)
        expected = base64.b64decode(digest_text.encode("ascii"), validate=True)

        if not salt or not expected:
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            _password_bytes(password),
            salt,
            iterations,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError, UnicodeEncodeError):
        return False