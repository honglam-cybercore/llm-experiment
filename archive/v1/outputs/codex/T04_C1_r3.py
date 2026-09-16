import hashlib
import hmac
import secrets

_ITERATIONS = 600_000
_SALT_BYTES = 16
_DK_BYTES = 32
_ALGORITHM = "pbkdf2_sha256"


def _password_bytes(password):
    if isinstance(password, str):
        return password.encode("utf-8")
    if isinstance(password, bytes):
        return password
    raise TypeError("password must be str or bytes")


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_DK_BYTES,
    )
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored) -> bool:
    try:
        password_bytes = _password_bytes(password)
        if not isinstance(stored, str):
            return False

        algorithm, iterations_text, salt_text, digest_text = stored.split("$")
        if algorithm != _ALGORITHM:
            return False

        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_text)
        expected_digest = bytes.fromhex(digest_text)

        if iterations <= 0 or len(salt) != _SALT_BYTES or len(expected_digest) != _DK_BYTES:
            return False

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt,
            iterations,
            dklen=len(expected_digest),
        )
        return hmac.compare_digest(actual_digest, expected_digest)
    except (TypeError, ValueError):
        return False