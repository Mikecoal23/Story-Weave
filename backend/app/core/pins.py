import base64
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet

from app.core.config import settings

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LENGTH = 32


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        pin.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_LENGTH
    )
    salt_text = base64.urlsafe_b64encode(salt).decode()
    digest_text = base64.urlsafe_b64encode(digest).decode()
    return f"scrypt${_SCRYPT_N}${salt_text}${digest_text}"


def verify_pin(pin: str, encoded_hash: str) -> bool:
    algorithm, n, salt_text, digest_text = encoded_hash.split("$", maxsplit=3)
    if algorithm != "scrypt":
        raise ValueError("Unsupported PIN hash algorithm")
    salt = base64.urlsafe_b64decode(salt_text)
    expected = base64.urlsafe_b64decode(digest_text)
    actual = hashlib.scrypt(
        pin.encode(), salt=salt, n=int(n), r=_SCRYPT_R, p=_SCRYPT_P, dklen=len(expected)
    )
    return hmac.compare_digest(actual, expected)


def _fernet() -> Fernet:
    if not settings.pin_encryption_key:
        raise RuntimeError("PIN_ENCRYPTION_KEY must be configured to use child PINs")
    try:
        return Fernet(settings.pin_encryption_key.encode())
    except (ValueError, TypeError) as error:
        raise RuntimeError("PIN_ENCRYPTION_KEY must be a valid Fernet key") from error


def encrypt_pin(pin: str) -> str:
    return _fernet().encrypt(pin.encode()).decode()


def decrypt_pin(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
