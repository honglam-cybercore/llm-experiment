import base64
import hashlib
import hmac
import secrets


_ITERATIONS = 600_000
_SALT_BYTES = 16
_KEY_BYTES = 32


def hash_password(password) -> str:
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    salt = secrets.token_bytes(_SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
        dklen=_KEY_BYTES,
    )

    return "pbkdf2_sha256${}${}${}".format(
        _ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(derived_key).decode("ascii"),
    )


def verify_password(password, stored) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False

    try:
        algorithm, iterations_text, salt_text, key_text = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)
        if iterations <= 0:
            return False

        salt = base64.b64decode(salt_text.encode("ascii"), validate=True)
        expected_key = base64.b64decode(key_text.encode("ascii"), validate=True)
    except (ValueError, TypeError):
        return False

    actual_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected_key),
    )
    return hmac.compare_digest(actual_key, expected_key)