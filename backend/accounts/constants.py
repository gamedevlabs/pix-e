from typing import Dict

from django.db import models


class ProviderType(models.TextChoices):
    OPENAI = "openai", "OpenAI"
    GEMINI = "gemini", "Gemini"
    MORPHEUS = "morpheus", "Morpheus (TUM CIT)"
    CUSTOM = "custom", "Custom API (OpenAI-compatible)"


# Default API base URLs for known providers.
# use this when adding new OpenAI compatible providers
# Single source of truth — import this, don't duplicate.
PROVIDER_DEFAULT_BASE_URLS: Dict[str, str] = {
    "morpheus": "https://morpheus.cit.tum.de/api",
}

