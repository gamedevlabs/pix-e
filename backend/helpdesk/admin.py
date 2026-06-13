import json

from django.contrib import admin
from django.utils.html import format_html

from .models import BackendSessionLog


@admin.register(BackendSessionLog)
class BackendSessionLogAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "highest_level",
        "event_count",
        "first_entry_at",
        "last_entry_at",
        "created_at",
    )
    search_fields = ("session_id",)
    list_filter = ("highest_level", "created_at")

    readonly_fields = (
        "session_id",
        "highest_level",
        "event_count",
        "first_entry_at",
        "last_entry_at",
        "created_at",
        "formatted_entries",
    )

    fields = (
        "session_id",
        "highest_level",
        "event_count",
        "first_entry_at",
        "last_entry_at",
        "created_at",
        "formatted_entries",
    )

    @admin.display(description="Entries")
    def formatted_entries(self, obj):
        return format_html(
            '<pre style="white-space: pre-wrap; font-size: 12px; line-height: 1.4;">{}</pre>',
            json.dumps(obj.entries, indent=2, ensure_ascii=False),
        )