from django.contrib import admin

from .models import UserApiKey


@admin.register(UserApiKey)
class UserApiKeyAdmin(admin.ModelAdmin):
    """
    Admin view for API key metadata.

    ⚠️  Never expose the raw key or encrypted_key in admin.
    ⚠️  encrypted_key is excluded from all admin views.
    """

    list_display = [
        "user",
        "provider",
        "label",
        "masked_key",
        "is_active",
        "disabled_reason",
        "last_used_at",
        "created_at",
    ]
    list_filter = ["provider", "is_active", "disabled_reason", "created_at"]
    search_fields = ["user__username", "user__email", "label"]
    readonly_fields = [
        "key_fingerprint",
        "masked_key",
        "last_used_at",
        "created_at",
        "updated_at",
    ]
    # encrypted_key is intentionally omitted from readonly_fields and fieldsets.
    # It's a BinaryField that renders as raw bytes — admins don't need it;
    # the fingerprint and masked key provide sufficient identification.
    fieldsets = [
        (
            "Identity",
            {
                "fields": ["user", "provider", "label"],
            },
        ),
        (
            "Security",
            {
                "fields": ["key_fingerprint", "masked_key"],
                "classes": ["collapse"],
                "description": "Sensitive fields — encrypted_key excluded",
            },
        ),
        (
            "Status",
            {
                "fields": ["is_active", "disabled_reason", "base_url", "last_used_at"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
