"""
Shared utilities for Django management commands that need LLM access.

Management commands have no user session, so they cannot retrieve the
encryption key from the session. Instead, they accept a --user argument
and prompt for the user's password to derive the encryption key,
enabling decryption of the user's stored API keys.
"""

import getpass
import sys
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

from accounts.encryption import derive_encryption_key
from accounts.models import UserSalt
from llm.providers.manager import ModelManager

User = get_user_model()


def add_user_argument(parser: CommandParser) -> None:
    """Add --user argument to a management command parser."""
    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="Username whose API keys to use for LLM operations",
    )
    parser.add_argument(
        "--password-from-stdin",
        action="store_true",
        help="Read password from stdin instead of prompting (for scripting)",
    )


def get_model_manager_for_user(
    *,
    username: str,
    password_from_stdin: bool = False,
    password: Optional[str] = None,
) -> ModelManager:
    """
    Create a ModelManager for a user by prompting for their password.

    Derives the Fernet encryption key from the password via PBKDF2
    and uses it to decrypt the user's stored API keys.

    Args:
        username: Username of the user whose API keys to use.
        password_from_stdin: If True, read password from stdin.
        password: If provided, use this password instead of prompting.

    Returns:
        ModelManager configured with the user's API keys.

    Raises:
        User.DoesNotExist: If the user doesn't exist.
        UserSalt.DoesNotExist: If the user has no encryption salt.
    """
    user = User.objects.get(username=username)

    if password is None:
        if password_from_stdin:
            password = sys.stdin.readline().strip()
        else:
            password = getpass.getpass(f"Enter password for {username}: ")

    try:
        user_salt = UserSalt.objects.get(user=user)
    except UserSalt.DoesNotExist:
        print(
            f"Error: User '{username}' has no encryption salt. "
            "They must log in via the web UI at least once to generate one.",
            file=sys.stderr,
        )
        raise

    assert password is not None, "Password should have been set above"
    enc_key = derive_encryption_key(password, bytes(user_salt.salt))
    return ModelManager.for_user(user, enc_key)
