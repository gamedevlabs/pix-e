import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .constants import ProviderType
from .encryption import encrypt_api_key, get_encryption_key_from_session
from .models import UserApiKey
from .validation import validate_key_format


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserApiKeySerializer(serializers.ModelSerializer):
    """Serializer for listing/creating API keys.

    IMPORTANT: Never expose the raw key in responses.
    The `key` write-only field accepts the plaintext key on creation
    but is NEVER included in response data.
    """

    key = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=500,
        help_text="The raw API key (write-only, never returned)",
    )
    masked_key = serializers.SerializerMethodField(
        read_only=True,
        help_text="Masked display (only last 4 chars visible)",
    )

    class Meta:
        model = UserApiKey
        fields = [
            "id",
            "provider",
            "label",
            "base_url",
            "is_active",
            "disabled_reason",
            "key",  # write-only
            "masked_key",  # read-only
            "last_used_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "masked_key",
            "last_used_at",
            "created_at",
            "updated_at",
        ]

    def get_masked_key(self, obj: UserApiKey) -> str:
        return obj.get_masked_key()

    def validate(self, attrs):
        if attrs.get("provider") == ProviderType.CUSTOM and not attrs.get("base_url"):
            raise serializers.ValidationError(
                {"base_url": "Base URL is required for custom (OpenAI-compatible) APIs"}
            )
        return attrs

    def update(self, instance, validated_data):
        # Block manual re-enable of auth-failure keys without a new key.
        if (
            instance.disabled_reason == "auth_failure"
            and validated_data.get("is_active") is True
            and "key" not in validated_data
        ):
            raise serializers.ValidationError(
                {
                    "is_active": (
                        "This key was disabled because the provider rejected it. "
                        "Enter a new API key value to re-enable it."
                    )
                }
            )

        # Allow key edits ONLY if the key is disabled due to auth failure.
        # This lets users fix a broken/invalid key without deleting it.
        if "key" in validated_data:
            if not instance.disabled_reason:
                raise serializers.ValidationError(
                    {
                        "key": "The API key cannot be changed on an active key. "
                        "Delete and re-create this key instead."
                    }
                )
            # Re-keying a disabled key: encrypt the new key, clear the failure
            raw_key = validated_data.pop("key")
            request = self.context.get("request")
            enc_key = get_encryption_key_from_session(request.session)
            if not enc_key:
                raise serializers.ValidationError(
                    {"key": "Session expired. Please log in again."}
                )
            validated_data["encrypted_key"] = encrypt_api_key(raw_key, enc_key)
            validated_data["is_active"] = True
            validated_data["disabled_reason"] = ""
            # Recompute fingerprint and masked_key
            pepper = settings.API_KEY_FINGERPRINT_PEPPER or ""
            validated_data["key_fingerprint"] = hmac.new(
                pepper.encode("utf-8"),
                raw_key.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            validated_data["masked_key"] = (
                f"\u2022\u2022\u2022\u2022{raw_key[-4:]}"
                if len(raw_key) >= 4
                else "\u2022\u2022\u2022\u2022"
            )
        return super().update(instance, validated_data)

    def create(self, validated_data):
        raw_key = validated_data.pop("key")
        request = self.context.get("request")

        # Pre-validate key format before encrypting
        is_valid, error_msg = validate_key_format(
            validated_data.get("provider", ""), raw_key
        )
        if not is_valid:
            raise serializers.ValidationError({"key": error_msg})

        # Encrypt the key BEFORE storing
        enc_key = get_encryption_key_from_session(request.session)
        if not enc_key:
            raise serializers.ValidationError(
                {"key": "Session expired. Please log in again."}
            )
        encrypted = encrypt_api_key(raw_key, enc_key)

        # Compute HMAC fingerprint for same-user dedup
        pepper = settings.API_KEY_FINGERPRINT_PEPPER or ""
        key_fingerprint = hmac.new(
            pepper.encode("utf-8"),
            raw_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Pre-compute masked key to avoid decrypting on every read
        masked_key = (
            f"\u2022\u2022\u2022\u2022{raw_key[-4:]}"
            if len(raw_key) >= 4
            else "\u2022\u2022\u2022\u2022"
        )

        with transaction.atomic():
            existing = UserApiKey.objects.filter(
                user=request.user,
                key_fingerprint=key_fingerprint,
            ).first()
            if existing:
                raise serializers.ValidationError(
                    {
                        "key": "You already have this API key saved as "
                        f"'{existing.label}'. Each key can only be added once."
                    }
                )

            return UserApiKey.objects.create(
                encrypted_key=encrypted,
                key_fingerprint=key_fingerprint,
                masked_key=masked_key,
                **validated_data,
            )
