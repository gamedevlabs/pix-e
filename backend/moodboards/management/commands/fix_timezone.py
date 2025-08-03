from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from moodboards.models import Moodboard, MoodboardImage, MoodboardComment


class Command(BaseCommand):
    help = 'Fix timezone-naive datetime fields in moodboard models'
    
    def handle(self, *args, **options):
        self.stdout.write('Fixing timezone-naive datetime fields...')
        
        # Count records to update
        moodboards_count = 0
        images_count = 0
        comments_count = 0
        
        # Fix Moodboard records
        for moodboard in Moodboard.objects.all():
            updated = False
            
            # Fix created_at if naive
            if moodboard.created_at and timezone.is_naive(moodboard.created_at):
                moodboard.created_at = timezone.make_aware(moodboard.created_at)
                updated = True
                
            # Fix updated_at if naive
            if moodboard.updated_at and timezone.is_naive(moodboard.updated_at):
                moodboard.updated_at = timezone.make_aware(moodboard.updated_at)
                updated = True
                
            if updated:
                moodboard.save(update_fields=['created_at', 'updated_at'])
                moodboards_count += 1
        
        # Fix MoodboardImage records
        for image in MoodboardImage.objects.all():
            updated = False
            
            if image.created_at and timezone.is_naive(image.created_at):
                image.created_at = timezone.make_aware(image.created_at)
                updated = True
                
            if image.updated_at and timezone.is_naive(image.updated_at):
                image.updated_at = timezone.make_aware(image.updated_at)
                updated = True
                
            if updated:
                image.save(update_fields=['created_at', 'updated_at'])
                images_count += 1
        
        # Fix MoodboardComment records
        for comment in MoodboardComment.objects.all():
            updated = False
            
            if comment.created_at and timezone.is_naive(comment.created_at):
                comment.created_at = timezone.make_aware(comment.created_at)
                updated = True
                
            if comment.updated_at and timezone.is_naive(comment.updated_at):
                comment.updated_at = timezone.make_aware(comment.updated_at)
                updated = True
                
            if updated:
                comment.save(update_fields=['created_at', 'updated_at'])
                comments_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated timezone fields:\n'
                f'  - {moodboards_count} moodboards\n'
                f'  - {images_count} images\n'
                f'  - {comments_count} comments'
            )
        )
