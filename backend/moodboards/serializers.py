from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Moodboard,
    MoodboardComment,
    MoodboardImage,
    MoodboardShare,
    MoodboardTemplate,
    MoodboardTextElement,
)


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer for nested relations"""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]
        read_only_fields = ["id", "username", "email"]


class MoodboardImageSerializer(serializers.ModelSerializer):
    """Serializer for MoodboardImage"""

    tag_list = serializers.ReadOnlyField()

    class Meta:
        model = MoodboardImage
        fields = [
            "id",
            "moodboard",
            "image_url",
            "thumbnail_url",
            "original_filename",
            "prompt",
            "generation_params",
            "title",
            "description",
            "source",
            "tags",
            "tag_list",
            "is_selected",
            "order_index",
            # Canvas positioning fields
            "x_position",
            "y_position",
            "canvas_width",
            "canvas_height",
            "rotation",
            "z_index",
            "opacity",
            # Technical metadata
            "width",
            "height",
            "file_size",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "tag_list"]

    def validate_order_index(self, value):
        """Ensure order_index is not negative"""
        if value < 0:
            raise serializers.ValidationError("Order index cannot be negative")
        return value


class MoodboardImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MoodboardImage with minimal required fields"""

    image_file = serializers.ImageField(required=False, write_only=True)

    class Meta:
        model = MoodboardImage
        fields = [
            "id",
            "image_url",
            "image_file",
            "prompt",
            "title",
            "description",
            "source",
            "tags",
            "is_selected",
            "order_index",
            "x_position",
            "y_position",
            "canvas_width",
            "canvas_height",
            "z_index",
            "opacity",
        ]
        extra_kwargs = {
            "image_url": {"required": False},
            "prompt": {"required": False},
            "title": {"required": False},
            "description": {"required": False},
            "tags": {"required": False},
        }

    def create(self, validated_data):
        image_file = validated_data.pop("image_file", None)

        if image_file:
            # Handle file upload
            import os
            import uuid

            from django.core.files.storage import default_storage

            # Generate unique filename
            ext = os.path.splitext(image_file.name)[1]
            filename = f"moodboard_{uuid.uuid4()}{ext}"

            # Save file
            file_path = default_storage.save(filename, image_file)
            validated_data["image_url"] = f"/media/{file_path}"
            validated_data["original_filename"] = image_file.name

        return super().create(validated_data)


class MoodboardTextElementSerializer(serializers.ModelSerializer):
    """Serializer for MoodboardTextElement"""

    class Meta:
        model = MoodboardTextElement
        fields = [
            "id",
            "moodboard",
            "content",
            # Canvas positioning
            "x_position",
            "y_position",
            "width",
            "height",
            "rotation",
            "z_index",
            "opacity",
            # Typography
            "font_family",
            "font_size",
            "font_weight",
            "text_align",
            "line_height",
            "letter_spacing",
            # Colors
            "text_color",
            "background_color",
            "border_color",
            "border_width",
            # State
            "is_selected",
            "order_index",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "moodboard", "created_at", "updated_at"]


class MoodboardCommentSerializer(serializers.ModelSerializer):
    """Serializer for MoodboardComment"""

    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = MoodboardComment
        fields = [
            "id",
            "user",
            "content",
            "image",
            "parent",
            "created_at",
            "updated_at",
            "replies",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "replies"]

    def get_replies(self, obj):
        """Get nested replies (only one level deep to avoid infinite recursion)"""
        if obj.replies.exists():
            return MoodboardCommentSerializer(
                obj.replies.all(), many=True, context=self.context
            ).data
        return []


class MoodboardShareSerializer(serializers.ModelSerializer):
    """Serializer for MoodboardShare"""

    user = UserSerializer(read_only=True)
    shared_by = UserSerializer(read_only=True)

    class Meta:
        model = MoodboardShare
        fields = ["user", "permission", "shared_at", "shared_by"]
        read_only_fields = ["user", "shared_at", "shared_by"]


class MoodboardSerializer(serializers.ModelSerializer):
    """General purpose Moodboard serializer for legacy compatibility"""

    user = UserSerializer(read_only=True)
    images = MoodboardImageSerializer(many=True, read_only=True)
    text_elements = MoodboardTextElementSerializer(many=True, read_only=True)
    image_count = serializers.ReadOnlyField()
    selected_image_count = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()

    class Meta:
        model = Moodboard
        fields = [
            "id",
            "user",
            "title",
            "description",
            "category",
            "status",
            "tags",
            "tag_list",
            "is_public",
            "color_palette",
            # Canvas settings
            "canvas_width",
            "canvas_height",
            "canvas_background_color",
            "canvas_background_image",
            "grid_enabled",
            "grid_size",
            "snap_to_grid",
            # Related objects
            "images",
            "text_elements",
            "image_count",
            "selected_image_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "images",
            "text_elements",
            "image_count",
            "selected_image_count",
            "tag_list",
            "created_at",
            "updated_at",
        ]


class MoodboardListSerializer(serializers.ModelSerializer):
    """Serializer for listing moodboards (minimal data)"""

    user = UserSerializer(read_only=True)
    images = MoodboardImageSerializer(many=True, read_only=True)
    image_count = serializers.ReadOnlyField()
    selected_image_count = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()

    class Meta:
        model = Moodboard
        fields = [
            "id",
            "user",
            "title",
            "description",
            "category",
            "status",
            "tags",
            "tag_list",
            "is_public",
            "images",
            "image_count",
            "selected_image_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "images",
            "image_count",
            "selected_image_count",
            "tag_list",
            "created_at",
            "updated_at",
        ]


class SharedMoodboardSerializer(serializers.ModelSerializer):
    """Serializer for moodboards shared with the current user"""

    user = UserSerializer(read_only=True)
    images = MoodboardImageSerializer(many=True, read_only=True)
    image_count = serializers.ReadOnlyField()
    selected_image_count = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    permission = serializers.SerializerMethodField()
    shared_by = serializers.SerializerMethodField()
    shared_at = serializers.SerializerMethodField()

    class Meta:
        model = Moodboard
        fields = [
            "id",
            "user",
            "title",
            "description",
            "category",
            "status",
            "tags",
            "tag_list",
            "is_public",
            "images",
            "image_count",
            "selected_image_count",
            "permission",
            "shared_by",
            "shared_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "images",
            "image_count",
            "selected_image_count",
            "tag_list",
            "permission",
            "shared_by",
            "shared_at",
            "created_at",
            "updated_at",
        ]

    def get_permission(self, obj):
        """Get the user's permission for this shared moodboard"""
        request = self.context.get("request")
        if request and request.user:
            try:
                share = MoodboardShare.objects.get(moodboard=obj, user=request.user)
                return share.permission
            except MoodboardShare.DoesNotExist:
                return None
        return None

    def get_shared_by(self, obj):
        """Get who shared this moodboard with the current user"""
        request = self.context.get("request")
        if request and request.user:
            try:
                share = MoodboardShare.objects.get(moodboard=obj, user=request.user)
                return UserSerializer(share.shared_by).data
            except MoodboardShare.DoesNotExist:
                return None
        return None

    def get_shared_at(self, obj):
        """Get when this moodboard was shared with the current user"""
        request = self.context.get("request")
        if request and request.user:
            try:
                share = MoodboardShare.objects.get(moodboard=obj, user=request.user)
                return share.shared_at
            except MoodboardShare.DoesNotExist:
                return None
        return None


class MoodboardDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed moodboard view"""

    user = UserSerializer(read_only=True)
    images = MoodboardImageSerializer(many=True, read_only=True)
    selected_images = serializers.SerializerMethodField()
    unselected_images = serializers.SerializerMethodField()
    comments = MoodboardCommentSerializer(many=True, read_only=True)
    shared_with = MoodboardShareSerializer(
        many=True, read_only=True, source="moodboardshare_set"
    )
    image_count = serializers.ReadOnlyField()
    selected_image_count = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()

    class Meta:
        model = Moodboard
        fields = [
            "id",
            "user",
            "title",
            "description",
            "category",
            "status",
            "tags",
            "tag_list",
            "color_palette",
            "is_public",
            "images",
            "selected_images",
            "unselected_images",
            "comments",
            "shared_with",
            "image_count",
            "selected_image_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "images",
            "selected_images",
            "unselected_images",
            "comments",
            "shared_with",
            "image_count",
            "selected_image_count",
            "tag_list",
            "created_at",
            "updated_at",
        ]

    def get_selected_images(self, obj):
        """Get only selected images"""
        selected_images = obj.images.filter(is_selected=True)
        return MoodboardImageSerializer(
            selected_images, many=True, context=self.context
        ).data

    def get_unselected_images(self, obj):
        """Get only unselected images"""
        unselected_images = obj.images.filter(is_selected=False)
        return MoodboardImageSerializer(
            unselected_images, many=True, context=self.context
        ).data


class MoodboardCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating moodboards"""

    class Meta:
        model = Moodboard
        fields = [
            "id",
            "title",
            "description",
            "category",
            "status",
            "tags",
            "color_palette",
            "is_public",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "tags": {"required": False},
        }

    def validate_color_palette(self, value):
        """Validate color palette format"""
        if value is not None:
            if not isinstance(value, list):
                raise serializers.ValidationError("Color palette must be a list")
            for color in value:
                if not isinstance(color, str):
                    raise serializers.ValidationError("Each color must be a string")
                if not (color.startswith("#") and len(color) == 7):
                    raise serializers.ValidationError(
                        "Colors must be in hex format (#RRGGBB)"
                    )
        return value


class MoodboardTemplateSerializer(serializers.ModelSerializer):
    """Serializer for MoodboardTemplate"""

    created_by = UserSerializer(read_only=True)

    class Meta:
        model = MoodboardTemplate
        fields = [
            "id",
            "title",
            "description",
            "template_type",
            "category",
            "default_prompts",
            "default_tags",
            "default_color_palette",
            "created_by",
            "is_active",
            "usage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "usage_count",
            "created_at",
            "updated_at",
        ]


class MoodboardBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on moodboards"""

    ACTION_CHOICES = [
        ("delete", "Delete"),
        ("archive", "Archive"),
        ("unarchive", "Unarchive"),
        ("duplicate", "Duplicate"),
        ("change_status", "Change Status"),
        ("add_tags", "Add Tags"),
        ("remove_tags", "Remove Tags"),
    ]

    moodboard_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of moodboard IDs to perform action on",
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)

    # Optional parameters for specific actions
    new_status = serializers.CharField(required=False, max_length=20)
    tags_to_add = serializers.CharField(required=False, max_length=500)
    tags_to_remove = serializers.CharField(required=False, max_length=500)

    def validate(self, data):
        """Cross-field validation"""
        action = data.get("action")

        if action == "change_status" and not data.get("new_status"):
            raise serializers.ValidationError(
                {"new_status": "This field is required when action is change_status"}
            )

        if action == "add_tags" and not data.get("tags_to_add"):
            raise serializers.ValidationError(
                {"tags_to_add": "This field is required when action is add_tags"}
            )

        if action == "remove_tags" and not data.get("tags_to_remove"):
            raise serializers.ValidationError(
                {"tags_to_remove": "This field is required when action is remove_tags"}
            )

        return data


class ImageBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on moodboard images"""

    ACTION_CHOICES = [
        ("select", "Select Images"),
        ("unselect", "Unselect Images"),
        ("delete", "Delete Images"),
        ("reorder", "Reorder Images"),
        ("add_tags", "Add Tags"),
        ("remove_tags", "Remove Tags"),
    ]

    image_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of image IDs to perform action on",
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)

    # Optional parameters
    new_order_indices = serializers.ListField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        help_text="New order indices for reorder action",
    )
    tags_to_add = serializers.CharField(required=False, max_length=500)
    tags_to_remove = serializers.CharField(required=False, max_length=500)

    def validate(self, data):
        """Cross-field validation"""
        action = data.get("action")
        image_ids = data.get("image_ids", [])

        if action == "reorder":
            new_order_indices = data.get("new_order_indices", [])
            if len(new_order_indices) != len(image_ids):
                raise serializers.ValidationError(
                    {
                        "new_order_indices": (
                            "Must provide same number of indices as image IDs"
                        )
                    }
                )

        if action == "add_tags" and not data.get("tags_to_add"):
            raise serializers.ValidationError(
                {"tags_to_add": "This field is required when action is add_tags"}
            )

        if action == "remove_tags" and not data.get("tags_to_remove"):
            raise serializers.ValidationError(
                {"tags_to_remove": "This field is required when action is remove_tags"}
            )

        return data
