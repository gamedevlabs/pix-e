from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Moodboard, MoodboardImage, MoodboardComment
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Moodboard)
def moodboard_saved(sender, instance, created, **kwargs):
    """Handle moodboard save events"""
    if created:
        logger.info(
            f"New moodboard created: {instance.title} by {instance.user.username}"
        )
    else:
        logger.info(f"Moodboard updated: {instance.title}")

    # Clear user's moodboard cache
    cache_key = f"user_moodboards_{instance.user.id}"
    cache.delete(cache_key)


@receiver(post_save, sender=MoodboardImage)
def moodboard_image_saved(sender, instance, created, **kwargs):
    """Handle moodboard image save events"""
    # Update moodboard's updated_at timestamp
    instance.moodboard.save(update_fields=["updated_at"])

    if created:
        logger.info(f"New image added to moodboard: {instance.moodboard.title}")


@receiver(pre_delete, sender=MoodboardImage)
def moodboard_image_deleted(sender, instance, **kwargs):
    """Handle moodboard image deletion"""
    logger.info(f"Image deleted from moodboard: {instance.moodboard.title}")

    # You could add cleanup logic here, such as:
    # - Deleting the actual image file from storage
    # - Updating related statistics
    # - Sending notifications


@receiver(post_save, sender=MoodboardComment)
def moodboard_comment_saved(sender, instance, created, **kwargs):
    """Handle moodboard comment events"""
    if created:
        logger.info(f"New comment added to moodboard: {instance.moodboard.title}")

        # You could add notification logic here
        # - Send email to moodboard owner
        # - Create in-app notification
        # - Update activity feed
