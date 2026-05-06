import uuid

from django.conf import settings
from django.db import models

from .constants import ProviderType


class UserApiKey(models.Model):
    """
    Stores encrypted API keys per user.
    The raw key is NEVER stored — only encrypted ciphertext.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    provider = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
        db_index=True,
    )
    label = models.CharField(
        max_length=100,
        help_text="User-friendly name (e.g. 'My Work OpenAI')",
    )
    encrypted_key = models.BinaryField(
        help_text="Fernet-encrypted API key bytes",
    )
    key_fingerprint = models.CharField(
        max_length=64,
        help_text="HMAC-SHA256 fingerprint of raw key (for duplicate detection)",
        blank=True,
        db_index=True,
    )
    masked_key = models.CharField(
        max_length=20,
        help_text="Pre-computed masked display key (e.g. '\u2022\u2022\u2022\u2022abcd')",
    )
    base_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Custom API base URL — e.g. https://api.openai.com/v1 (NOT the completions endpoint)",
    )
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User API Key"
        verbose_name_plural = "User API Keys"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "label"],
                name="unique_user_key_label",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "is_active"], name="user_api_keys_active_idx"),
        ]

    def __str__(self):
        return f"{self.user.username} / {self.provider} / {self.label}"

    def get_masked_key(self) -> str:
        """Return pre-computed masked key (no decrypt needed)."""
        return self.masked_key
