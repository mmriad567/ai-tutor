import os
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
    """
    Load the ENCRYPTION_KEY from environment and return a Fernet instance.
    Raises ValueError if the key is missing or invalid.
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY is missing. Add it to your .env file. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise ValueError(f"ENCRYPTION_KEY is invalid: {e}")


def encrypt_key(plain_text: str) -> str:
    """
    Encrypt a plain API key and return the encrypted string (safe to store in DB).
    """
    if not plain_text:
        raise ValueError("Cannot encrypt an empty string.")
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_text.encode())
    return encrypted.decode()


def decrypt_key(encrypted_text: str) -> str:
    """
    Decrypt an encrypted API key. Returns the original plain text.
    Raises ValueError if the data was tampered with or the key is wrong.
    """
    if not encrypted_text:
        raise ValueError("Cannot decrypt an empty string.")
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except InvalidToken:
        raise ValueError(
            "Failed to decrypt. The ENCRYPTION_KEY may have changed, or the data is corrupted."
        )


def mask_key(plain_text: str, visible_chars: int = 4) -> str:
    """
    Show only the last few characters of a key for safe display.
    Example: AIzaSyB1234567890abcdef → '****cdef'
    """
    if not plain_text:
        return ""
    if len(plain_text) <= visible_chars:
        return "*" * len(plain_text)
    return "*" * (len(plain_text) - visible_chars) + plain_text[-visible_chars:]
