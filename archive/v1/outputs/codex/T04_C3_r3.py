import base64
import hashlib
import hmac
import secrets


_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_LENGTH = 16
_DIGEST_LENGTH = hashlib.sha256().digest_size
_MAX_STORED_LENGTH = 512


def _password_bytes(password):
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    try:
        return password.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("password contains invalid characters") from exc


def hash_password(password) -> str:
    password_bytes = _password_bytes(password)
    salt = secrets.token_bytes(_SALT_LENGTH)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_DIGEST_LENGTH,
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
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    if len(stored) > _MAX_STORED_LENGTH:
        return False

    try:
        algorithm, iteration_text, salt_text, digest_text = stored.split("$")
        if algorithm != _ALGORITHM:
            return False

        iterations = int(iteration_text)
        if iterations < 100_000 or iterations > 10_000_000:
            return False

        salt = base64.b64decode(salt_text.encode("ascii"), validate=True)
        expected_digest = base64.b64decode(
            digest_text.encode("ascii"), validate=True
        )
        if len(salt) != _SALT_LENGTH or len(expected_digest) != _DIGEST_LENGTH:
            return False

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=_DIGEST_LENGTH,
        )
        return hmac.compare_digest(actual_digest, expected_digest)
    except (ValueError, TypeError, UnicodeEncodeError, UnicodeDecodeError):
        return False
