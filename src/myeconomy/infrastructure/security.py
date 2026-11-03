"""Password hashing and opaque session-token primitives."""

from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_password_hasher = PasswordHasher()
# A precomputed dummy hash reduces the username-enumeration timing difference.
_dummy_password_hash = _password_hasher.hash("not-a-real-user-password-never-use")


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    target_hash = encoded_hash or _dummy_password_hash
    try:
        valid = _password_hasher.verify(target_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return bool(valid and encoded_hash)


def password_hash_needs_rehash(encoded_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(encoded_hash)


def issue_session_token() -> str:
    """Generate a 256-bit opaque bearer token; only its digest is persisted."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
