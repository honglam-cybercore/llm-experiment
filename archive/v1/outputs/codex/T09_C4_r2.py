from cryptography.fernet import Fernet, InvalidToken


def generate_key() -> bytes:
    return Fernet.generate_key()


def encrypt(plaintext, key) -> bytes:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a str")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")

    try:
        cipher = Fernet(key)
    except Exception as exc:
        raise ValueError("invalid encryption key") from exc

    return cipher.encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext, key) -> str:
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")

    try:
        cipher = Fernet(key)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError, TypeError) as exc:
        raise ValueError("invalid key or ciphertext") from exc