"""
API key encryption at rest.

Security model
--------------
The Fernet key is DERIVED FROM THE USER'S PLAINTEXT PASSWORD at login time
and stored ONLY in the server-side Django session (never persisted).

Key expiry is tracked INDEPENDENTLY from the Django session via a UTC
timestamp in the session. This means:
- The Django session can stay alive for days (user stays logged in | configurable)
- The encryption key expires after KEY_TTL_SECONDS (30s for testing)
  or when logging out or when closing the tab
- When the key expires, the user gets a password prompt to re-derive it
- The ReestablishKeyView only needs the password, not a new login
"""

import base64
import logging
import os
import time
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# OWASP-recommended iterations for PBKDF2-HMAC-SHA256 as of 2024.
# Source: https://cheatsheetseries.owasp.org/cheatsheets/
#   Password_Storage_Cheat_Sheet.html#pbkdf2
# Current recommendation: 600_000 iterations (updated Dec 2023).
_PBKDF2_ITERATIONS = 600_000
_SESSION_KEY_NAME = "user_encryption_key"
_SESSION_EXPIRES_AT_NAME = "user_encryption_key_expires_at"
KEY_TTL_SECONDS = 30  # 30 seconds — intentionally short for testing


def derive_encryption_key(plaintext_password: str, salt: bytes) -> bytes:
    """
    Derive a Fernet key from the user's plaintext password and a per-user salt.

    Args:
        plaintext_password: The user's plaintext password.
        salt: Per-user random salt (16 bytes). Must be read from
              ``UserSalt.salt`` — Django's ``BinaryField`` returns a
              ``memoryview``, so callers need ``bytes(user_salt.salt)``.

    Returns:
        URL-safe-base64-encoded Fernet key (32 raw bytes → 44 base64 bytes).
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(plaintext_password.encode("utf-8")))


def generate_encryption_salt() -> bytes:
    """Generate a cryptographically random 16-byte salt for a new user."""
    return os.urandom(16)


def store_key_in_session(session, key: bytes) -> None:
    """Store the encryption key in the session with its own expiry timestamp."""
    session[_SESSION_KEY_NAME] = key.decode("utf-8")
    session[_SESSION_EXPIRES_AT_NAME] = time.time() + KEY_TTL_SECONDS


def get_encryption_key_from_session(session) -> Optional[bytes]:
    """
    Extract the user's encryption key from the Django session.

    Checks BOTH:
    - Whether the key exists in the session
    - Whether the key's independent TTL has expired

    On every successful read, the key's TTL is refreshed (bumped forward
    by KEY_TTL_SECONDS), so active users stay authenticated for API key
    operations without re-entering their password every hour.

    Returns None if the key is missing or expired.
    The Django session itself may still be valid (user is logged in).
    """
    key = session.get(_SESSION_KEY_NAME)
    expires_at = session.get(_SESSION_EXPIRES_AT_NAME)

    if not key or not expires_at:
        return None

    if time.time() > expires_at:
        # Key expired — clear it so we don't check again
        session.pop(_SESSION_KEY_NAME, None)
        session.pop(_SESSION_EXPIRES_AT_NAME, None)
        return None

    # Only extend the TTL if at least 10s has elapsed since last bump
    # to avoid unnecessary session mutations on every read.
    if expires_at - time.time() < KEY_TTL_SECONDS - 10:
        session[_SESSION_EXPIRES_AT_NAME] = time.time() + KEY_TTL_SECONDS
    return key.encode("utf-8")


def clear_key_from_session(session) -> None:
    """Remove the encryption key and its expiry from the session."""
    session.pop(_SESSION_KEY_NAME, None)
    session.pop(_SESSION_EXPIRES_AT_NAME, None)


def encrypt_api_key(plaintext: str, encryption_key: bytes) -> bytes:
    """Encrypt a raw API key using the user's session-derived Fernet key."""
    if not plaintext:
        raise ValueError("Cannot encrypt empty value")
    if not encryption_key:
        raise RuntimeError("Encryption key not available — user must log in")

    f = Fernet(encryption_key)
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_api_key(ciphertext: bytes, encryption_key: bytes) -> str:
    """Decrypt a Fernet-encrypted API key."""
    if not ciphertext:
        raise ValueError("Cannot decrypt empty value")
    if not encryption_key:
        raise RuntimeError("Encryption key not available — user must log in")

    f = Fernet(encryption_key)
    return f.decrypt(ciphertext).decode("utf-8")
