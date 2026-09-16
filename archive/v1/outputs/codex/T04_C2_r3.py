import base64
import hashlib
import hmac
import secrets


_ITERATIONS = 600_000
_SALT_BYTES = 16
_DK_BYTES = 32
_ALGORITHM = "pbkdf2_sha256"


def hash_password(password) -> str:
    if isinstance(password, str):
        password = password.encode("utf-8")
    elif not isinstance(password, (bytes, bytearray)):
        raise TypeError("password must be a string or bytes")

    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", bytes(password), salt, _ITERATIONS, dklen=_DK_BYTES
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
    if isinstance(password, str):
        password = password.encode("utf-8")
    elif isinstance(password, (bytes, bytearray)):
        password = bytes(password)
    else:
        return False

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

        actual = hashlib.pbkdf2_hmac(
            "sha256", password, salt, iterations, dklen=len(expected)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False