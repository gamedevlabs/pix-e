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
        "last_used_at",
        "created_at",
    ]
    list_filter = ["provider", "is_active", "created_at"]
    search_fields = ["user__username", "user__email", "label"]
    readonly_fields = [
        "encrypted_key",
        "key_fingerprint",
        "masked_key",
        "last_used_at",
        "created_at",
        "updated_at",
    ]
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
                "fields": ["encrypted_key", "key_fingerprint", "masked_key"],
                "classes": ["collapse"],
                "description": "Sensitive fields — encrypted_key is stored ciphertext only",
            },
        ),
        (
            "Status",
            {
                "fields": ["is_active", "base_url", "last_used_at"],
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
