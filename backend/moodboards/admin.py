from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Moodboard,
    MoodboardComment,
    MoodboardImage,
    MoodboardShare,
    MoodboardTemplate,
)


class MoodboardImageInline(admin.TabularInline):
    """Inline admin for moodboard images"""

    model = MoodboardImage
    extra = 0
    fields = [
        "image_url",
        "title",
        "is_selected",
        "order_index",
        "source",
        "created_at",
    ]
    readonly_fields = ["created_at"]
    ordering = ["order_index", "created_at"]


class MoodboardShareInline(admin.TabularInline):
    """Inline admin for moodboard sharing"""

    model = MoodboardShare
    extra = 0
    fields = ["user", "permission", "shared_by", "shared_at"]
    readonly_fields = ["shared_at"]


class MoodboardCommentInline(admin.TabularInline):
    """Inline admin for moodboard comments"""

    model = MoodboardComment
    extra = 0
    fields = ["user", "content", "image", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Moodboard)
class MoodboardAdmin(admin.ModelAdmin):
    """Admin interface for Moodboard"""

    list_display = [
        "title",
        "user",
        "category",
        "status",
        "image_count_display",
        "is_public",
        "created_at",
        "updated_at",
    ]
    list_filter = ["category", "status", "is_public", "created_at"]
    search_fields = ["title", "description", "tags", "user__username"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "image_count_display",
        "selected_image_count_display",
    ]

    fieldsets = [
        (
            "Basic Information",
            {"fields": ["id", "user", "title", "description", "category", "status"]},
        ),
        ("Settings", {"fields": ["is_active", "is_public"]}),
        ("Content", {"fields": ["tags", "color_palette"]}),
        (
            "Statistics",
            {
                "fields": ["image_count_display", "selected_image_count_display"],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    inlines = [MoodboardImageInline, MoodboardShareInline, MoodboardCommentInline]

    actions = [
        "make_public",
        "make_private",
        "archive_moodboards",
        "activate_moodboards",
    ]

    @admin.display(description="Images")
    def image_count_display(self, obj):
        """Display image count with link to images"""
        count = obj.image_count
        if count > 0:
            url = (
                reverse("admin:moodboards_moodboardimage_changelist")
                + f"?moodboard__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} images</a>', url, count)
        return "0 images"

    @admin.display(description="Selected Images")
    @admin.display(description="Selected Images")
    def selected_image_count_display(self, obj):
        """Display selected image count"""
        return f"{obj.selected_image_count} selected"

    @admin.action(description="Make selected moodboards public")
    def make_public(self, request, queryset):
        """Action to make moodboards public"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} moodboards made public.")

    def make_private(self, request, queryset):
        """Action to make moodboards private"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f"{updated} moodboards made private.")

    def archive_moodboards(self, request, queryset):
        """Action to archive moodboards"""
        updated = queryset.update(status="archived")
        self.message_user(request, f"{updated} moodboards archived.")

    def activate_moodboards(self, request, queryset):
        """Action to activate moodboards"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} moodboards activated.")


@admin.register(MoodboardImage)
class MoodboardImageAdmin(admin.ModelAdmin):
    """Admin interface for MoodboardImage"""

    list_display = [
        "title_or_id",
        "moodboard",
        "source",
        "is_selected",
        "order_index",
        "image_preview",
        "created_at",
    ]
    list_filter = ["source", "is_selected", "created_at", "moodboard__category"]
    search_fields = ["title", "description", "prompt", "moodboard__title", "tags"]
    readonly_fields = ["id", "created_at", "updated_at", "image_preview"]

    fieldsets = [
        ("Basic Information", {"fields": ["id", "moodboard", "title", "description"]}),
        (
            "Image Data",
            {
                "fields": [
                    "image_url",
                    "thumbnail_url",
                    "image_preview",
                    "original_filename",
                ]
            },
        ),
        (
            "AI Generation",
            {"fields": ["prompt", "generation_params"], "classes": ["collapse"]},
        ),
        ("Metadata", {"fields": ["source", "tags", "is_selected", "order_index"]}),
        (
            "Properties",
            {"fields": ["width", "height", "file_size"], "classes": ["collapse"]},
        ),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    actions = ["select_images", "unselect_images", "move_to_top", "move_to_bottom"]

    def title_or_id(self, obj):
        """Display title or ID if no title"""
        return obj.title or f"Image {str(obj.id)[:8]}"

    def image_preview(self, obj):
        """Display image preview"""
        if obj.thumbnail_url:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.thumbnail_url,
            )
        elif obj.image_url:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image_url,
            )
        return "No image"

    def select_images(self, request, queryset):
        """Action to select images"""
        updated = queryset.update(is_selected=True)
        self.message_user(request, f"{updated} images selected.")

    def unselect_images(self, request, queryset):
        """Action to unselect images"""
        updated = queryset.update(is_selected=False)
        self.message_user(request, f"{updated} images unselected.")

    def move_to_top(self, request, queryset):
        """Action to move images to top"""
        for obj in queryset:
            obj.order_index = 0
            obj.save()
        self.message_user(request, f"{queryset.count()} images moved to top.")

    def move_to_bottom(self, request, queryset):
        """Action to move images to bottom"""
        for obj in queryset:
            obj.order_index = 9999
            obj.save()
        self.message_user(request, f"{queryset.count()} images moved to bottom.")


@admin.register(MoodboardShare)
class MoodboardShareAdmin(admin.ModelAdmin):
    """Admin interface for MoodboardShare"""

    list_display = ["moodboard", "user", "permission", "shared_by", "shared_at"]
    list_filter = ["permission", "shared_at"]
    search_fields = ["moodboard__title", "user__username", "shared_by__username"]
    readonly_fields = ["shared_at"]

    fieldsets = [
        (
            "Sharing Information",
            {"fields": ["moodboard", "user", "permission", "shared_by"]},
        ),
        ("Timestamps", {"fields": ["shared_at"], "classes": ["collapse"]}),
    ]


@admin.register(MoodboardComment)
class MoodboardCommentAdmin(admin.ModelAdmin):
    """Admin interface for MoodboardComment"""

    list_display = ["content_preview", "moodboard", "user", "image", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "moodboard__title", "user__username"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = [
        (
            "Comment Information",
            {"fields": ["id", "moodboard", "user", "image", "parent"]},
        ),
        ("Content", {"fields": ["content"]}),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    def content_preview(self, obj):
        """Display content preview"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content


@admin.register(MoodboardTemplate)
class MoodboardTemplateAdmin(admin.ModelAdmin):
    """Admin interface for MoodboardTemplate"""

    list_display = [
        "title",
        "template_type",
        "category",
        "created_by",
        "usage_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["template_type", "category", "is_active", "created_at"]
    search_fields = ["title", "description", "created_by__username"]
    readonly_fields = ["id", "usage_count", "created_at", "updated_at"]

    fieldsets = [
        (
            "Basic Information",
            {"fields": ["id", "title", "description", "template_type", "category"]},
        ),
        (
            "Template Data",
            {"fields": ["default_prompts", "default_tags", "default_color_palette"]},
        ),
        ("Metadata", {"fields": ["created_by", "is_active", "usage_count"]}),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    actions = ["activate_templates", "deactivate_templates", "reset_usage_count"]

    def activate_templates(self, request, queryset):
        """Action to activate templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} templates activated.")

    def deactivate_templates(self, request, queryset):
        """Action to deactivate templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} templates deactivated.")

    def reset_usage_count(self, request, queryset):
        """Action to reset usage count"""
        updated = queryset.update(usage_count=0)
        self.message_user(request, f"Usage count reset for {updated} templates.")
