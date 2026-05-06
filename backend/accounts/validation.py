"""
Key validation utilities.

Separate from encryption module so validation can be used
without the cryptography dependency in import path.
"""

import re
from typing import Tuple

# Compiled regex patterns for provider-specific key format validation.
# OpenAI keys: start with "sk-" followed by 20+ alphanumeric chars.
# Gemini keys: start with "AIza" followed by 10+ alphanumeric/dash/underscore chars.
OPENAI_KEY_PATTERN = re.compile(r"^sk-[A-Za-z0-9]{20,}$")
GEMINI_KEY_PATTERN = re.compile(r"^AIza[A-Za-z0-9_-]{10,}$")


def validate_key_format(provider: str, key: str) -> Tuple[bool, str]:
    """
    Two-tier key validation.

    Tier 1 — Syntactic (instant, no network):
    - Check prefix matches known patterns via regex
    - Check minimum length
    - Check no whitespace

    Tier 2 — Semantic (network call):
    - Handled by test_provider_connection() in views.py

    Returns (is_valid, error_message).
    """
    if not key or not key.strip():
        return False, "API key is required"

    if key != key.strip():
        return False, "API key contains leading or trailing whitespace"

    if provider in ("openai", "morpheus"):
        if not OPENAI_KEY_PATTERN.match(key):
            return False, (
                f"{provider.title()} keys typically start with 'sk-' "
                "followed by at least 20 alphanumeric characters"
            )

    elif provider == "gemini":
        if not GEMINI_KEY_PATTERN.match(key):
            return False, (
                "Gemini keys typically start with 'AIza' "
                "followed by at least 10 characters"
            )

    elif provider == "custom":
        if len(key) < 8:
            return False, "Custom API key must be at least 8 characters"

    return True, ""
