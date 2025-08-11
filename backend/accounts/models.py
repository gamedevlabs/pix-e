from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os


class AIServiceToken(models.Model):
    """Store AI service tokens for users"""

    SERVICE_CHOICES = [
        ("huggingface", "Hugging Face"),
        ("github", "GitHub Models"),
        ("google", "Google Gemini"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_tokens")
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    encrypted_token = models.TextField()  # Store encrypted token
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "service_type")
        verbose_name = "AI Service Token"
        verbose_name_plural = "AI Service Tokens"

    def __str__(self):
        return f"{self.user.username} - {self.get_service_type_display()}"

    @property
    def encryption_key(self):
        """Get or create encryption key for this user"""
        key = getattr(settings, "AI_TOKEN_ENCRYPTION_KEY", None)
        if not key:
            # Generate a key if not set
            key = Fernet.generate_key()
        return key

    def encrypt_token(self, token):
        """Encrypt the token before storing"""
        f = Fernet(self.encryption_key)
        return f.encrypt(token.encode()).decode()

    def decrypt_token(self):
        """Decrypt the stored token"""
        try:
            f = Fernet(self.encryption_key)
            return f.decrypt(self.encrypted_token.encode()).decode()
        except Exception:
            return None

    def set_token(self, token):
        """Set and encrypt the token"""
        self.encrypted_token = self.encrypt_token(token)

    def get_token(self):
        """Get the decrypted token"""
        return self.decrypt_token()

    @property
    def masked_token(self):
        """Return a masked version of the token for display"""
        token = self.get_token()
        if token and len(token) > 8:
            return f"{token[:4]}...{token[-4:]}"
        return "****" if token else "Not set"

    def clean(self):
        if not self.encrypted_token.strip():
            raise ValidationError("Token cannot be empty")
