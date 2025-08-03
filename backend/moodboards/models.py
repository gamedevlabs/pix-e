from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import json


class MoodboardManager(models.Manager):
    """Custom manager for Moodboard with enhanced querying capabilities"""
    
    def get_user_moodboards(self, user):
        """Get all moodboards accessible to a user (owned + shared)"""
        return self.filter(
            models.Q(user=user) | models.Q(shared_with=user)
        ).distinct()
    
    def get_public_moodboards(self):
        """Get all public moodboards"""
        return self.filter(is_public=True, status__in=['completed', 'in_progress'])
    
    def get_active_drafts(self, user, max_age_days=7):
        """Get active drafts for a user (cleanup old ones)"""
        cutoff_date = timezone.now() - timezone.timedelta(days=max_age_days)
        return self.filter(
            user=user, 
            status='draft', 
            updated_at__gte=cutoff_date
        )


class Moodboard(models.Model):
    """
    Production-ready Moodboard model with comprehensive features
    
    This replaces the dual session/moodboard system with a unified approach:
    - All work starts as a draft moodboard
    - Real-time auto-save eliminates need for sessions
    - Clear state transitions from draft to completed
    - Built-in permission and sharing system
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),           # Auto-created, unsaved work
        ('in_progress', 'In Progress'), # Saved but still being worked on
        ('completed', 'Completed'),   # Finalized moodboard
        ('archived', 'Archived'),     # Hidden from normal views
    ]
    
    CATEGORY_CHOICES = [
        ('gaming', 'Gaming'),
        ('ui_ux', 'UI/UX Design'),
        ('concept_art', 'Concept Art'),
        ('character_design', 'Character Design'),
        ('environment', 'Environment Design'),
        ('product_design', 'Product Design'),
        ('branding', 'Branding & Identity'),
        ('architecture', 'Architecture'),
        ('fashion', 'Fashion Design'),
        ('other', 'Other'),
    ]
    
    PUBLIC_PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Edit Access'),
    ]
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='moodboards',
        help_text='Owner of the moodboard'
    )
    
    # Metadata
    title = models.CharField(
        max_length=255, 
        default='Untitled Moodboard',
        validators=[MinLengthValidator(1), MaxLengthValidator(255)],
        help_text='Moodboard title (1-255 characters)'
    )
    description = models.TextField(
        blank=True, 
        max_length=2000,
        help_text='Brief description of the moodboard concept (max 2000 chars)'
    )
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='other',
        db_index=True,
        help_text='Moodboard category for organization'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        db_index=True,
        help_text='Current status of the moodboard'
    )
    
    # Tagging and organization
    tags = models.CharField(
        max_length=500, 
        blank=True, 
        help_text='Comma-separated tags for searching and organization'
    )
    color_palette = models.JSONField(
        blank=True, 
        null=True, 
        help_text='Saved color palette as JSON array of hex colors'
    )
    
    # Sharing and permissions
    is_public = models.BooleanField(
        default=False, 
        db_index=True,
        help_text='Make this moodboard publicly viewable'
    )
    public_permission = models.CharField(
        max_length=10,
        choices=PUBLIC_PERMISSION_CHOICES,
        default='view',
        help_text='Permission level for public access'
    )
    shared_with = models.ManyToManyField(
        User, 
        through='MoodboardShare', 
        through_fields=('moodboard', 'user'),
        related_name='shared_moodboards', 
        blank=True,
        help_text='Users this moodboard is explicitly shared with'
    )
    
    # Analytics and engagement
    view_count = models.PositiveIntegerField(default=0, help_text='Number of times viewed')
    like_count = models.PositiveIntegerField(default=0, help_text='Number of likes received')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_accessed = models.DateTimeField(
        default=timezone.now,
        help_text='Last time this moodboard was accessed'
    )
    
    # Manager
    objects = MoodboardManager()
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['category', 'is_public']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_public', 'status']),
            models.Index(fields=['updated_at']),
        ]
        constraints = [
            # Note: Complex constraints can be added later via raw SQL if needed
        ]
    
    def __str__(self):
        return f"{self.title} by {self.user.username} ({self.get_status_display()})"
    
    def clean(self):
        """Validate model data"""
        super().clean()
        
        # Validate color palette format
        if self.color_palette:
            try:
                if not isinstance(self.color_palette, list):
                    raise ValidationError({'color_palette': 'Must be a list of colors'})
                
                for color in self.color_palette:
                    if not isinstance(color, str) or not color.startswith('#'):
                        raise ValidationError({'color_palette': 'All colors must be hex strings'})
            except (TypeError, ValueError) as e:
                raise ValidationError({'color_palette': 'Invalid color palette format'})
    
    def save(self, *args, **kwargs):
        self.clean()
        self.last_accessed = timezone.now()
        super().save(*args, **kwargs)
    
    # Properties for computed values
    @property
    def image_count(self):
        """Get the total number of images in this moodboard"""
        return self.images.count()
    
    @property
    def selected_image_count(self):
        """Get the number of selected images in this moodboard"""
        return self.images.filter(is_selected=True).count()
    
    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    @property
    def is_draft(self):
        """Check if this is a draft moodboard"""
        return self.status == 'draft'
    
    @property
    def is_collaborative(self):
        """Check if this moodboard allows collaboration"""
        return self.is_public and self.public_permission == 'edit'
    
    # Methods for tag management
    def add_tag(self, tag):
        """Add a tag to the moodboard"""
        if not tag or not tag.strip():
            return False
            
        current_tags = self.tag_list
        tag = tag.strip().lower()
        
        if tag not in [t.lower() for t in current_tags]:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
            self.save(update_fields=['tags'])
            return True
        return False
    
    def remove_tag(self, tag):
        """Remove a tag from the moodboard"""
        if not tag:
            return False
            
        current_tags = self.tag_list
        tag = tag.strip().lower()
        
        # Case-insensitive removal
        updated_tags = [t for t in current_tags if t.lower() != tag]
        
        if len(updated_tags) != len(current_tags):
            self.tags = ', '.join(updated_tags)
            self.save(update_fields=['tags'])
            return True
        return False
    
    def add_color_to_palette(self, color):
        """Add a color to the palette"""
        if not color or not color.startswith('#'):
            return False
            
        palette = self.color_palette or []
        
        if color not in palette and len(palette) < 10:  # Max 10 colors
            palette.append(color)
            self.color_palette = palette
            self.save(update_fields=['color_palette'])
            return True
        return False
    
    def remove_color_from_palette(self, color):
        """Remove a color from the palette"""
        if not self.color_palette or color not in self.color_palette:
            return False
            
        palette = self.color_palette.copy()
        palette.remove(color)
        self.color_palette = palette
        self.save(update_fields=['color_palette'])
        return True
    
    # Permission methods
    def can_user_view(self, user):
        """Check if user can view this moodboard"""
        if not user.is_authenticated:
            return self.is_public
        
        return (
            self.user == user or 
            self.is_public or 
            self.shared_with.filter(id=user.id).exists()
        )
    
    def can_user_edit(self, user):
        """Check if user can edit this moodboard"""
        if not user.is_authenticated:
            return False
        
        if self.user == user:
            return True
        
        # Check explicit sharing permissions
        share = self.shares.filter(user=user).first()
        if share and share.permission in ['edit', 'admin']:
            return True
        
        # Check public edit permission
        return self.is_public and self.public_permission == 'edit'
    
    def can_user_delete(self, user):
        """Check if user can delete this moodboard"""
        return user.is_authenticated and self.user == user
    
    def can_user_share(self, user):
        """Check if user can share this moodboard"""
        return user.is_authenticated and self.user == user
    
    # Analytics methods
    def increment_view_count(self):
        """Increment view count atomically"""
        Moodboard.objects.filter(id=self.id).update(
            view_count=models.F('view_count') + 1,
            last_accessed=timezone.now()
        )
    
    def increment_like_count(self):
        """Increment like count atomically"""
        Moodboard.objects.filter(id=self.id).update(
            like_count=models.F('like_count') + 1
        )
    
    # State transition methods
    def mark_as_in_progress(self):
        """Transition from draft to in_progress"""
        if self.status == 'draft':
            self.status = 'in_progress'
            self.save(update_fields=['status'])
    
    def mark_as_completed(self):
        """Mark moodboard as completed"""
        if self.status in ['draft', 'in_progress']:
            self.status = 'completed'
            self.save(update_fields=['status'])
    
    def archive(self):
        """Archive the moodboard"""
        self.status = 'archived'
        self.save(update_fields=['status'])

class MoodboardImageManager(models.Manager):
    """Custom manager for MoodboardImage with enhanced querying"""
    
    def get_selected_images(self, moodboard):
        """Get all selected images for a moodboard"""
        return self.filter(moodboard=moodboard, is_selected=True).order_by('order_index')
    
    def get_unselected_images(self, moodboard):
        """Get all unselected images for a moodboard"""
        return self.filter(moodboard=moodboard, is_selected=False).order_by('-created_at')
    
    def bulk_update_selection(self, moodboard, image_ids, is_selected=True):
        """Bulk update selection status for multiple images"""
        return self.filter(
            moodboard=moodboard, 
            id__in=image_ids
        ).update(is_selected=is_selected)


class MoodboardImage(models.Model):
    """
    Production-ready MoodboardImage model with enhanced metadata and capabilities
    
    This model stores all images related to a moodboard, whether generated,
    uploaded, or imported. It includes comprehensive metadata for search,
    organization, and optimization.
    """
    
    SOURCE_CHOICES = [
        ('ai_generated', 'AI Generated'),
        ('uploaded', 'User Uploaded'),
        ('url_import', 'Imported from URL'),
        ('stock', 'Stock Image'), 
        ('template', 'Template Image'),
    ]
    
    GENERATION_STATUS_CHOICES = [
        ('pending', 'Generation Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moodboard = models.ForeignKey(
        Moodboard, 
        on_delete=models.CASCADE, 
        related_name='images',
        help_text='Parent moodboard'
    )
    
    # Image data and storage
    image_url = models.CharField(
        max_length=1000, 
        help_text='URL or path to the full-size image'
    )
    thumbnail_url = models.CharField(
        max_length=1000, 
        blank=True, 
        help_text='URL or path to optimized thumbnail'
    )
    original_filename = models.CharField(
        max_length=255, 
        blank=True,
        help_text='Original filename if uploaded'
    )
    
    # Content and metadata
    title = models.CharField(
        max_length=255, 
        blank=True,
        help_text='Custom title for the image'
    )
    description = models.TextField(
        blank=True,
        max_length=1000,
        help_text='Description or notes about the image'
    )
    prompt = models.TextField(
        blank=True, 
        help_text='AI prompt used to generate this image'
    )
    
    # AI generation metadata
    generation_params = models.JSONField(
        blank=True, 
        null=True, 
        help_text='Parameters used for AI generation (model, seed, etc.)'
    )
    generation_status = models.CharField(
        max_length=20,
        choices=GENERATION_STATUS_CHOICES,
        default='completed',
        help_text='Status of AI generation process'
    )
    generation_time = models.FloatField(
        null=True,
        blank=True,
        help_text='Time taken to generate image in seconds'
    )
    
    # Classification and organization
    source = models.CharField(
        max_length=20, 
        choices=SOURCE_CHOICES, 
        default='ai_generated',
        db_index=True,
        help_text='Source/method of image creation'
    )
    tags = models.CharField(
        max_length=500, 
        blank=True,
        help_text='Comma-separated tags for search and organization'
    )
    
    # State and positioning
    is_selected = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether image is selected for the final moodboard'
    )
    order_index = models.PositiveIntegerField(
        default=0, 
        help_text='Order position in the moodboard'
    )
    
    # Technical metadata
    width = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Image width in pixels'
    )
    height = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Image height in pixels'
    )
    file_size = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text='File size in bytes'
    )
    format = models.CharField(
        max_length=10,
        blank=True,
        help_text='Image format (PNG, JPG, etc.)'
    )
    
    # Color and style analysis
    dominant_colors = models.JSONField(
        blank=True,
        null=True,
        help_text='Dominant colors extracted from image as hex values'
    )
    style_tags = models.JSONField(
        blank=True,
        null=True,
        help_text='Automatically detected style characteristics'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager
    objects = MoodboardImageManager()
    
    class Meta:
        ordering = ['order_index', 'created_at']
        indexes = [
            models.Index(fields=['moodboard', 'is_selected']),
            models.Index(fields=['source', 'generation_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['moodboard', 'order_index']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(order_index__gte=0),
                name='image_order_index_positive'
            ),
        ]
    
    def __str__(self):
        title = self.title or self.prompt[:50] if self.prompt else f"Image {str(self.id)[:8]}"
        return f"{title} in {self.moodboard.title}"
    
    def clean(self):
        """Validate model data"""
        super().clean()
        
        # Validate generation parameters
        if self.generation_params:
            try:
                if not isinstance(self.generation_params, dict):
                    raise ValidationError({'generation_params': 'Must be a valid JSON object'})
            except (TypeError, ValueError) as e:
                raise ValidationError({'generation_params': 'Invalid JSON format'})
        
        # Validate image dimensions
        if self.width is not None and self.width <= 0:
            raise ValidationError({'width': 'Width must be positive'})
        if self.height is not None and self.height <= 0:
            raise ValidationError({'height': 'Height must be positive'})
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    # Properties
    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    @property
    def aspect_ratio(self):
        """Calculate aspect ratio"""
        if self.width and self.height:
            return round(self.width / self.height, 2)
        return None
    
    @property
    def display_title(self):
        """Get display title (fallback to prompt or ID)"""
        return self.title or (self.prompt[:50] + '...' if len(self.prompt) > 50 else self.prompt) or f"Image {str(self.id)[:8]}"
    
    @property
    def is_ai_generated(self):
        """Check if image was AI generated"""
        return self.source == 'ai_generated'
    
    @property
    def is_processing(self):
        """Check if image is still being processed"""
        return self.generation_status in ['pending', 'processing']
    
    @property
    def generation_failed(self):
        """Check if generation failed"""
        return self.generation_status == 'failed'
    
    # Methods for tag management
    def add_tag(self, tag):
        """Add a tag to the image"""
        if not tag or not tag.strip():
            return False
            
        current_tags = self.tag_list
        tag = tag.strip().lower()
        
        if tag not in [t.lower() for t in current_tags]:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
            self.save(update_fields=['tags'])
            return True
        return False
    
    def remove_tag(self, tag):
        """Remove a tag from the image"""
        if not tag:
            return False
            
        current_tags = self.tag_list
        tag = tag.strip().lower()
        
        updated_tags = [t for t in current_tags if t.lower() != tag]
        
        if len(updated_tags) != len(current_tags):
            self.tags = ', '.join(updated_tags)
            self.save(update_fields=['tags'])
            return True
        return False
    
    # Selection and ordering methods
    def select(self, order_index=None):
        """Select this image for the moodboard"""
        self.is_selected = True
        if order_index is not None:
            self.order_index = order_index
        else:
            # Auto-assign next order index
            max_order = MoodboardImage.objects.filter(
                moodboard=self.moodboard,
                is_selected=True
            ).aggregate(models.Max('order_index'))['order_index__max']
            self.order_index = (max_order or 0) + 1
        self.save(update_fields=['is_selected', 'order_index'])
    
    def deselect(self):
        """Deselect this image from the moodboard"""
        self.is_selected = False
        self.order_index = 0
        self.save(update_fields=['is_selected', 'order_index'])
    
    def reorder(self, new_index):
        """Change the order index of this image"""
        if self.is_selected:
            old_index = self.order_index
            self.order_index = new_index
            self.save(update_fields=['order_index'])
            
            # Reorder other images if necessary
            if new_index != old_index:
                self._reorder_siblings(old_index, new_index)
    
    def _reorder_siblings(self, old_index, new_index):
        """Reorder sibling images when this image's order changes"""
        siblings = MoodboardImage.objects.filter(
            moodboard=self.moodboard,
            is_selected=True
        ).exclude(id=self.id)
        
        if new_index > old_index:
            # Moving down - shift others up
            siblings.filter(
                order_index__gt=old_index,
                order_index__lte=new_index
            ).update(order_index=models.F('order_index') - 1)
        else:
            # Moving up - shift others down
            siblings.filter(
                order_index__gte=new_index,
                order_index__lt=old_index
            ).update(order_index=models.F('order_index') + 1)


class MoodboardShare(models.Model):
    """
    Enhanced model for tracking moodboard sharing permissions
    
    This model handles explicit sharing relationships between users
    and moodboards, providing granular permission control.
    """
    
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'View and Edit'),
        ('admin', 'Full Access'), # Can manage sharing, but not delete
    ]
    
    moodboard = models.ForeignKey(
        Moodboard, 
        on_delete=models.CASCADE,
        related_name='shares',
        help_text='The moodboard being shared'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text='User receiving access'
    )
    permission = models.CharField(
        max_length=20, 
        choices=PERMISSION_CHOICES, 
        default='view',
        help_text='Level of access granted'
    )
    
    # Metadata
    shared_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When access was granted'
    )
    shared_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='shares_created',
        help_text='User who granted the access'
    )
    
    # Optional customization
    custom_message = models.TextField(
        blank=True,
        max_length=500,
        help_text='Custom message sent with the share invitation'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional expiration time for access'
    )
    
    class Meta:
        unique_together = ['moodboard', 'user']
        indexes = [
            models.Index(fields=['moodboard', 'permission']),
            models.Index(fields=['user', 'shared_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('shared_by')),
                name='cannot_share_with_self'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_permission_display()} on {self.moodboard.title}"
    
    @property
    def is_expired(self):
        """Check if this share has expired"""
        return self.expires_at and timezone.now() > self.expires_at
    
    def can_edit(self):
        """Check if this share allows editing"""
        return not self.is_expired and self.permission in ['edit', 'admin']
    
    def can_manage_sharing(self):
        """Check if this share allows managing other shares"""
        return not self.is_expired and self.permission == 'admin'


class MoodboardComment(models.Model):
    """
    Enhanced model for comments and collaboration on moodboards
    
    Supports threaded conversations and image-specific comments.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moodboard = models.ForeignKey(
        Moodboard, 
        on_delete=models.CASCADE, 
        related_name='comments',
        help_text='Moodboard this comment belongs to'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text='User who wrote the comment'
    )
    content = models.TextField(
        max_length=2000,
        help_text='Comment content (max 2000 characters)'
    )
    
    # Optional: Comment on specific image
    image = models.ForeignKey(
        MoodboardImage, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='comments',
        help_text='Specific image this comment relates to (optional)'
    )
    
    # Threading for replies
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        help_text='Parent comment for threading replies'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderation
    is_hidden = models.BooleanField(
        default=False,
        help_text='Hide comment (for moderation)'
    )
    hidden_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hidden_comments',
        help_text='User who hid this comment'
    )
    hidden_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When comment was hidden'
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['moodboard', 'created_at']),
            models.Index(fields=['image', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"Comment by {self.user.username}: {preview}"
    
    def clean(self):
        """Validate comment data"""
        super().clean()
        
        # Ensure image belongs to the same moodboard
        if self.image and self.image.moodboard != self.moodboard:
            raise ValidationError({'image': 'Image must belong to the same moodboard'})
        
        # Prevent deep nesting (max 3 levels)
        if self.parent:
            depth = 1
            current = self.parent
            while current.parent and depth < 3:
                current = current.parent
                depth += 1
            if depth >= 3:
                raise ValidationError({'parent': 'Comments can only be nested 3 levels deep'})
    
    @property
    def is_reply(self):
        """Check if this is a reply to another comment"""
        return self.parent is not None
    
    @property
    def reply_count(self):
        """Get number of direct replies"""
        return self.replies.filter(is_hidden=False).count()
    
    def hide(self, hidden_by_user):
        """Hide this comment"""
        self.is_hidden = True
        self.hidden_by = hidden_by_user
        self.hidden_at = timezone.now()
        self.save(update_fields=['is_hidden', 'hidden_by', 'hidden_at'])
    
    def unhide(self):
        """Unhide this comment"""
        self.is_hidden = False
        self.hidden_by = None
        self.hidden_at = None
        self.save(update_fields=['is_hidden', 'hidden_by', 'hidden_at'])


# Signal handlers for automatic cleanup and optimization
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=MoodboardImage)
def update_moodboard_timestamp(sender, instance, **kwargs):
    """Update moodboard timestamp when images are modified"""
    instance.moodboard.save(update_fields=['updated_at'])

@receiver(post_delete, sender=MoodboardImage) 
def cleanup_on_image_delete(sender, instance, **kwargs):
    """Clean up related data when image is deleted"""
    # Update moodboard timestamp
    if instance.moodboard_id:
        try:
            instance.moodboard.save(update_fields=['updated_at'])
        except Moodboard.DoesNotExist:
            pass

@receiver(post_save, sender=Moodboard)
def auto_cleanup_old_drafts(sender, instance, created, **kwargs):
    """Automatically clean up old draft moodboards"""
    if created and instance.status == 'draft':
        # Clean up old drafts for this user (keep only 5 most recent)
        old_drafts = Moodboard.objects.filter(
            user=instance.user,
            status='draft'
        ).exclude(id=instance.id).order_by('-updated_at')[5:]
        
        for draft in old_drafts:
            draft.delete()


class MoodboardTemplate(models.Model):
    """Model for moodboard templates that users can start from"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('starter', 'Starter Template'),
        ('category', 'Category Template'),
        ('style', 'Style Template'),
        ('mood', 'Mood Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='starter')
    category = models.CharField(max_length=20, choices=Moodboard.CATEGORY_CHOICES, default='other')
    
    # Template data
    default_prompts = models.JSONField(help_text='Default prompts for this template')
    default_tags = models.CharField(max_length=500, blank=True)
    default_color_palette = models.JSONField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-usage_count', 'title']
    
    def __str__(self):
        return f"Template: {self.title}"
    
    def increment_usage(self):
        """Increment the usage count when template is used"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
