"""
Key validation utilities.

Separate from encryption module so validation can be used
without the cryptography dependency in import path.
"""

import re
from typing import Tuple

# ── Provider-agnostic format validation ──────────────────────────


def validate_key_format(provider: str, key: str) -> Tuple[bool, str]:
    """
    Simple format validation: non-empty, no whitespace, minimum length.
    Provider-specific regex patterns are intentionally NOT used — they
    break when providers change their key format (e.g. new Gemini keys
    start with 'AQ.' instead of 'AIza').  The real validation happens
    via test_provider_connection() which actually calls the API.
    """
    if not key or not key.strip():
        return False, "API key is required"

    if key != key.strip():
        return False, "API key contains leading or trailing whitespace"

    if len(key) < 8:
        return False, "API key must be at least 8 characters"

    return True, ""


# ── API key sanitization ─────────────────────────────────────────

AUTH_FAILURE_PATTERNS = [
    r"\b401\b",
    r"\b403\b",
    "http 401",
    "http 403",
    "status 401",
    "status 403",
    "401 unauthorized",
    "403 forbidden",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "authentication failed",
    "permission denied",
    "not authorized",
    "auth error",
    "invalid authentication credentials",
    "api key not found",
    "credential",
]
_AUTH_FAILURE_REGEX = [re.compile(p, re.IGNORECASE) for p in AUTH_FAILURE_PATTERNS]


def should_auto_disable(error_message: str) -> bool:
    return any(patt.search(error_message) for patt in _AUTH_FAILURE_REGEX)


def sanitize_error_message(error_msg: str, api_key: str) -> str:
    if not api_key or not error_msg:
        return error_msg
    pattern = re.escape(api_key)
    error_msg = re.sub(pattern, "***", error_msg, flags=re.IGNORECASE)
    if len(api_key) >= 12:
        prefix = re.escape(api_key[:8])
        suffix = re.escape(api_key[-4:])
        truncated_pattern = prefix + r".*?" + suffix
        error_msg = re.sub(truncated_pattern, "***", error_msg, flags=re.IGNORECASE)
    return error_msg


# ── Provider connection testing ──────────────────────────────────


def test_provider_connection(provider: str, api_key: str, base_url: str = "") -> tuple:
    """
    Test an API key by making a minimal request to the provider.
    Returns (True, message) on success, (False, error_message) on failure.
    Error messages have the API key stripped to avoid leaking secrets.
    """
    try:
        if provider in ("openai", "custom"):
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url=base_url or None,
                timeout=15,
            )
            models = client.models.list()
            first_model = next((m.id for m in models if m.id), "gpt-4o-mini")
            client.chat.completions.create(
                model=first_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True, "Connected successfully."

        elif provider == "morpheus":
            import httpx

            base = (base_url or "https://morpheus.cit.tum.de/api").rstrip("/")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            with httpx.Client() as client:
                models_resp = client.get(
                    f"{base}/v1/models",
                    headers=headers,
                    timeout=15,
                )
                models_resp.raise_for_status()
                models_data = models_resp.json()
                first_model = next(
                    (m["id"] for m in models_data.get("data", []) if m.get("id")),
                    "ministral-3",
                )
                client.post(
                    f"{base}/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": first_model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1,
                    },
                    timeout=15,
                )
            return True, "Connected to Morpheus API."

        elif provider == "gemini":
            from google import genai

            gemini_client = genai.Client(api_key=api_key)
            gemini_models = list(gemini_client.models.list())
            first_model = next(
                (
                    m.name.split("/")[-1]
                    for m in gemini_models
                    if m.name and m.name.startswith("models/gemini")
                ),
                "gemini-2.5-flash",
            )
            gemini_client.models.generate_content(
                model=first_model,
                contents="test",
                config={"max_output_tokens": 1},
            )
            return True, "Connected to Gemini API."

        else:
            return False, f"Unknown provider: {provider}"

    except Exception as e:
        error_msg = sanitize_error_message(str(e), api_key)
        return False, error_msg
