"""Password hashing and verification using passlib."""
from __future__ import annotations

try:
    import bcrypt as bcrypt_lib
except ImportError:  # pragma: no cover - optional legacy compatibility
    bcrypt_lib = None

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("$2") and bcrypt_lib is not None:
        try:
            return bcrypt_lib.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False

    return pwd_context.verify(plain_password, hashed_password)
