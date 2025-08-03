from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from .models import (
    Moodboard, 
    MoodboardImage, 
    MoodboardShare, 
    MoodboardComment,
    MoodboardTemplate
)


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']


class MoodboardImageSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for MoodboardImage with all metadata
    """
    
    # Computed fields
    tag_list = serializers.ReadOnlyField()
    aspect_ratio = serializers.ReadOnlyField()
    display_title = serializers.ReadOnlyField()
    is_ai_generated = serializers.ReadOnlyField()
    is_processing = serializers.ReadOnlyField()
    generation_failed = serializers.ReadOnlyField()
    
    # Optional nested data
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MoodboardImage
        fields = [
            # Core fields
            'id', 'moodboard', 'image_url', 'thumbnail_url', 'original_filename',
            
            # Content
            'title', 'description', 'prompt',
            
            # Generation metadata
            'generation_params', 'generation_status', 'generation_time',
            
            # Classification
            'source', 'tags', 'tag_list',
            
            # State
            'is_selected', 'order_index',
            
            # Technical metadata
            'width', 'height', 'file_size', 'format', 'aspect_ratio',
            
            # Color and style
            'dominant_colors', 'style_tags',
            
            # Computed properties
            'display_title', 'is_ai_generated', 'is_processing', 'generation_failed',
            
            # Timestamps
            'created_at', 'updated_at',
            
            # Related data
            'comments_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        """Get number of comments on this image"""
        return obj.comments.filter(is_hidden=False).count()
    
    def validate_generation_params(self, value):
        """Validate generation parameters structure"""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Generation parameters must be a valid JSON object")
        return value
    
    def validate_dominant_colors(self, value):
        """Validate dominant colors format"""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError("Dominant colors must be a list")
            for color in value:
                if not isinstance(color, str) or not color.startswith('#'):
                    raise serializers.ValidationError("All colors must be hex strings starting with #")
        return value


class MoodboardImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new images with minimal required fields"""
    
    class Meta:
        model = MoodboardImage
        fields = [
            'moodboard', 'image_url', 'thumbnail_url', 'prompt', 
            'generation_params', 'source', 'is_selected', 'order_index',
            'width', 'height', 'file_size', 'format'
        ]
    
    def create(self, validated_data):
        """Create image with automatic order index if not provided"""
        if 'order_index' not in validated_data and validated_data.get('is_selected'):
            # Auto-assign next order index for selected images
            moodboard = validated_data['moodboard']
            max_order = MoodboardImage.objects.filter(
                moodboard=moodboard,
                is_selected=True
            ).aggregate(models.Max('order_index'))['order_index__max']
            validated_data['order_index'] = (max_order or 0) + 1
        
        return super().create(validated_data)


class MoodboardImageBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on multiple images"""
    
    ACTION_CHOICES = [
        ('select', 'Select Images'),
        ('deselect', 'Deselect Images'),
        ('delete', 'Delete Images'),
        ('reorder', 'Reorder Images'),
        ('tag', 'Add Tags'),
        ('untag', 'Remove Tags'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    image_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    
    # Optional parameters for specific actions
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="Tags to add/remove (for tag/untag actions)"
    )
    order_mapping = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        help_text="Mapping of image_id to new order_index (for reorder action)"
    )
    
    def validate(self, data):
        """Validate action-specific parameters"""
        action = data['action']
        
        if action in ['tag', 'untag'] and not data.get('tags'):
            raise serializers.ValidationError("Tags are required for tag/untag actions")
        
        if action == 'reorder' and not data.get('order_mapping'):
            raise serializers.ValidationError("Order mapping is required for reorder action")
        
        return data


class MoodboardShareSerializer(serializers.ModelSerializer):
    """Serializer for moodboard sharing permissions"""
    
    user = UserBasicSerializer(read_only=True)
    shared_by = UserBasicSerializer(read_only=True)
    is_expired = serializers.ReadOnlyField()
    can_edit = serializers.ReadOnlyField()
    can_manage_sharing = serializers.ReadOnlyField()
    
    class Meta:
        model = MoodboardShare
        fields = [
            'id', 'moodboard', 'user', 'permission', 'shared_at', 'shared_by',
            'custom_message', 'expires_at', 'is_expired', 'can_edit', 'can_manage_sharing'
        ]
        read_only_fields = ['id', 'shared_at']


class MoodboardCommentSerializer(serializers.ModelSerializer):
    """Serializer for moodboard comments with threading support"""
    
    user = UserBasicSerializer(read_only=True) 
    hidden_by = UserBasicSerializer(read_only=True)
    is_reply = serializers.ReadOnlyField()
    reply_count = serializers.ReadOnlyField()
    
    # Nested replies (limited depth to prevent deep recursion)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = MoodboardComment
        fields = [
            'id', 'moodboard', 'user', 'content', 'image', 'parent',
            'created_at', 'updated_at', 'is_hidden', 'hidden_by', 'hidden_at',
            'is_reply', 'reply_count', 'replies'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_hidden', 'hidden_by', 'hidden_at']
    
    def get_replies(self, obj):
        """Get direct replies to this comment (non-recursive for performance)"""
        if obj.is_reply:  # Don't nest replies to replies
            return []
        
        replies = obj.replies.filter(is_hidden=False).order_by('created_at')[:10]  # Limit replies
        return MoodboardCommentSerializer(replies, many=True, context=self.context).data


class MoodboardListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for moodboard listings"""
    
    user = UserBasicSerializer(read_only=True)
    
    # Computed fields
    image_count = serializers.ReadOnlyField()
    selected_image_count = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    is_draft = serializers.ReadOnlyField()
    is_collaborative = serializers.ReadOnlyField()
    
    # Preview data
    preview_images = serializers.SerializerMethodField()
    
    class Meta:
        model = Moodboard
        fields = [
            'id', 'user', 'title', 'description', 'category', 'status',
            'tags', 'tag_list', 'is_public', 'public_permission',
            'view_count', 'like_count', 'created_at', 'updated_at',
            'image_count', 'selected_image_count', 'is_draft', 'is_collaborative',
            'preview_images'
        ]
    
    def get_preview_images(self, obj):
        """Get preview images for list display"""
        preview_images = obj.images.filter(is_selected=True).order_by('order_index')[:4]
        return [{
            'id': img.id,
            'thumbnail_url': img.thumbnail_url or img.image_url,
            'title': img.display_title
        } for img in preview_images]


class MoodboardDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for detailed moodboard view"""
    
    user = UserBasicSerializer(read_only=True)
    
    # Related data
    images = MoodboardImageSerializer(many=True, read_only=True)
    shares = MoodboardShareSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    
    # Computed fields
    image_count = serializers.ReadOnlyField()
    selected_image_count = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    is_draft = serializers.ReadOnlyField()
    is_collaborative = serializers.ReadOnlyField()
    
    # User permissions
    user_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Moodboard
        fields = [
            # Core fields
            'id', 'user', 'title', 'description', 'category', 'status',
            
            # Organization
            'tags', 'tag_list', 'color_palette',
            
            # Sharing
            'is_public', 'public_permission', 'shared_with',
            
            # Analytics
            'view_count', 'like_count',
            
            # Timestamps
            'created_at', 'updated_at', 'last_accessed',
            
            # Computed properties
            'image_count', 'selected_image_count', 'is_draft', 'is_collaborative',
            
            # Related data
            'images', 'shares', 'comments',
            
            # User context
            'user_permissions',
        ]
    
    def get_comments(self, obj):
        """Get top-level comments with nested replies"""
        top_level_comments = obj.comments.filter(
            parent=None, 
            is_hidden=False
        ).order_by('-created_at')[:20]  # Limit comments for performance
        
        return MoodboardCommentSerializer(
            top_level_comments, 
            many=True, 
            context=self.context
        ).data
    
    def get_user_permissions(self, obj):
        """Get current user's permissions for this moodboard"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {
                'can_view': obj.is_public,
                'can_edit': False,
                'can_delete': False,
                'can_share': False
            }
        
        user = request.user
        return {
            'can_view': obj.can_user_view(user),
            'can_edit': obj.can_user_edit(user),
            'can_delete': obj.can_user_delete(user),
            'can_share': obj.can_user_share(user),
            'is_owner': obj.user == user
        }


class MoodboardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new moodboards"""
    
    class Meta:
        model = Moodboard
        fields = [
            'title', 'description', 'category', 'tags', 'color_palette',
            'is_public', 'public_permission'
        ]
    
    def validate_title(self, value):
        """Validate title is not empty after stripping"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_color_palette(self, value):
        """Validate color palette format"""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError("Color palette must be a list")
            if len(value) > 10:
                raise serializers.ValidationError("Color palette cannot have more than 10 colors")
            for color in value:
                if not isinstance(color, str) or not color.startswith('#'):
                    raise serializers.ValidationError("All colors must be hex strings starting with #")
        return value
    
    def create(self, validated_data):
        """Create moodboard with current user as owner"""
        request = self.context['request']
        validated_data['user'] = request.user
        return super().create(validated_data)


class MoodboardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing moodboards"""
    
    class Meta:
        model = Moodboard
        fields = [
            'title', 'description', 'category', 'status', 'tags', 
            'color_palette', 'is_public', 'public_permission'
        ]
    
    def validate_title(self, value):
        """Validate title is not empty after stripping"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status
            
            # Define allowed transitions
            allowed_transitions = {
                'draft': ['in_progress', 'completed', 'archived'],
                'in_progress': ['completed', 'archived'],
                'completed': ['in_progress', 'archived'],
                'archived': ['in_progress', 'completed']
            }
            
            if value != current_status and value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from {current_status} to {value}"
                )
        
        return value


class MoodboardBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on multiple moodboards"""
    
    ACTION_CHOICES = [
        ('delete', 'Delete Moodboards'),
        ('archive', 'Archive Moodboards'),
        ('unarchive', 'Unarchive Moodboards'),
        ('make_public', 'Make Public'),
        ('make_private', 'Make Private'),
        ('change_category', 'Change Category'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    moodboard_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=50
    )
    
    # Optional parameters for specific actions
    category = serializers.ChoiceField(
        choices=Moodboard.CATEGORY_CHOICES,
        required=False,
        help_text="New category (for change_category action)"
    )
    
    def validate(self, data):
        """Validate action-specific parameters"""
        action = data['action']
        
        if action == 'change_category' and not data.get('category'):
            raise serializers.ValidationError("Category is required for change_category action")
        
        return data


class MoodboardTemplateSerializer(serializers.ModelSerializer):
    """Serializer for moodboard templates"""
    
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MoodboardTemplate
        fields = [
            'id', 'created_by', 'title', 'description', 'template_type', 
            'category', 'template_data', 'preview_image', 'is_public', 
            'use_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'use_count', 'created_at', 'updated_at']
    
    def validate_template_data(self, value):
        """Validate template data structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Template data must be a valid JSON object")
        
        # Add specific validation based on template_type if needed
        return value
    
    def create(self, validated_data):
        """Create template with current user as creator"""
        request = self.context['request']
        validated_data['created_by'] = request.user
        return super().create(validated_data)


# Legacy serializers for backward compatibility
class ImageBulkActionSerializer(MoodboardImageBulkActionSerializer):
    """Legacy alias for backward compatibility"""
    pass

class MoodboardCreateUpdateSerializer(MoodboardUpdateSerializer):
    """Legacy alias for backward compatibility"""
    pass
