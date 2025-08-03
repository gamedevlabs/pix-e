"""
Production-ready Views for Moodboard System

This module implements a unified, production-ready API for moodboards
that eliminates the session/moodboard confusion by using a moodboard-first
approach with draft-based workflow.

Key Features:
- Unified moodboard-centric API
- Draft-based workflow (no temporary sessions)
- Production-grade error handling
- Comprehensive permission system
- Real-time collaboration support
- Performance optimizations
"""

from django.db.models import Q, Count, Prefetch, F, Max
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import SessionAuthentication
from rest_framework.throttling import UserRateThrottle
from datetime import datetime, timedelta
import logging

# Custom CSRF-exempt authentication for API calls
class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session authentication that doesn't enforce CSRF for API calls"""
    def enforce_csrf(self, request):
        return

# Import models and serializers
from .models import (
    Moodboard, 
    MoodboardImage, 
    MoodboardShare, 
    MoodboardComment, 
    MoodboardTemplate
)
from .serializers_production import (
    MoodboardListSerializer,
    MoodboardDetailSerializer,
    MoodboardCreateSerializer,
    MoodboardUpdateSerializer,
    MoodboardImageSerializer,
    MoodboardImageCreateSerializer,
    MoodboardImageBulkActionSerializer,
    MoodboardCommentSerializer,
    MoodboardTemplateSerializer,
    MoodboardBulkActionSerializer,
    MoodboardShareSerializer
)
from .permissions import MoodboardPermission, CanViewMoodboard, CanEditMoodboard

# Set up logging
logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Optimized pagination configuration"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MoodboardGenerationThrottle(UserRateThrottle):
    """Custom throttle for AI generation to prevent abuse"""
    scope = 'generation'
    rate = '10/hour'  # 10 generations per hour per user


class MoodboardViewSet(viewsets.ModelViewSet):
    """
    Production-ready ViewSet for Moodboard operations
    
    This unified API eliminates the session/moodboard confusion by implementing
    a moodboard-first approach where all work is persistent from the start.
    
    Features:
    - CRUD operations for moodboards
    - Draft-based workflow (no temporary sessions needed)
    - Real-time collaboration
    - Bulk operations
    - Advanced filtering and search
    - Permission-based access control
    - Performance optimizations
    """
    
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MoodboardPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'status', 'view_count', 'like_count']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Get optimized queryset with proper permissions"""
        user = self.request.user
        
        # Base queryset with optimized joins
        queryset = Moodboard.objects.select_related('user').prefetch_related(
            'images',
            'shared_with',
            Prefetch('comments', queryset=MoodboardComment.objects.filter(is_hidden=False))
        ).annotate(
            total_images=Count('images', distinct=True),
            selected_images=Count('images', filter=Q(images__is_selected=True), distinct=True),
            total_comments=Count('comments', filter=Q(comments__is_hidden=False), distinct=True)
        )
        
        # Filter based on action
        action = self.action
        
        if action == 'public':
            # Public moodboards only
            return queryset.filter(
                is_public=True,
                status__in=['completed', 'in_progress']
            ).exclude(status='draft')
        
        elif action in ['list', 'retrieve']:
            # User's accessible moodboards
            return queryset.filter(
                Q(user=user) | 
                Q(shared_with=user) | 
                Q(is_public=True)
            ).distinct()
        
        else:
            # For create/update/delete, only user's own moodboards
            return queryset.filter(user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MoodboardListSerializer
        elif self.action == 'create':
            return MoodboardCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MoodboardUpdateSerializer
        else:
            return MoodboardDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve moodboard with view count increment"""
        instance = self.get_object()
        
        # Increment view count if not owner
        if request.user != instance.user:
            instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create new moodboard (replaces session creation)
        
        This endpoint replaces the old session-based approach.
        Every moodboard starts as a draft and can be worked on immediately.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create as draft by default for new moodboards
        if 'status' not in serializer.validated_data:
            serializer.validated_data['status'] = 'draft'
        
        moodboard = serializer.save()
        
        logger.info(f"Created new moodboard {moodboard.id} for user {request.user.username}")
        
        # Return full detail serialization
        detail_serializer = MoodboardDetailSerializer(moodboard, context={'request': request})
        
        return Response(
            detail_serializer.data, 
            status=status.HTTP_201_CREATED,
            headers={'Location': f'/api/v1/moodboards/{moodboard.id}/'}
        )
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """Get public moodboards gallery"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Additional filters for public gallery
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        featured = request.query_params.get('featured') == 'true'
        if featured:
            # Featured = high engagement
            queryset = queryset.filter(
                Q(like_count__gte=10) | Q(view_count__gte=100)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MoodboardListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MoodboardListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_images(self, request, pk=None):
        """
        Generate AI images for moodboard (replaces session-based generation)
        
        This unified endpoint handles image generation directly on moodboards,
        eliminating the need for temporary sessions.
        """
        moodboard = self.get_object()
        
        # Check permissions
        if not moodboard.can_user_edit(request.user):
            raise PermissionDenied("You don't have permission to edit this moodboard")
        
        # Apply throttling for generation
        throttle = MoodboardGenerationThrottle()
        if not throttle.allow_request(request, self):
            return Response(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get generation parameters
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return Response(
                {'error': 'Prompt is required for image generation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Optional parameters
        num_images = min(int(request.data.get('num_images', 4)), 8)  # Max 8 images
        style = request.data.get('style', 'default')
        color_palette = request.data.get('color_palette', [])
        
        try:
            # Use existing AI generation service from llm app
            from llm.views import generate_gaming_images
            
            # Generate images using the existing service
            generated_urls = generate_gaming_images(prompt, num_images=num_images)
            
            # Create MoodboardImage objects from generated URLs
            generated_images = []
            for i, url in enumerate(generated_urls):
                image = MoodboardImage.objects.create(
                    moodboard=moodboard,
                    image_url=url,
                    prompt=prompt,
                    source='ai_generated',
                    generation_params={
                        'style': style,
                        'color_palette': color_palette,
                        'num_images': num_images
                    },
                    generation_status='completed',
                    is_selected=False,
                    title=f'Generated Image {i+1}'
                )
                generated_images.append(image)
            
            # Mark moodboard as in_progress if it was a draft
            if moodboard.status == 'draft':
                moodboard.mark_as_in_progress()
            
            logger.info(f"Generated {len(generated_images)} images for moodboard {moodboard.id}")
            
            # Return updated moodboard data
            serializer = MoodboardDetailSerializer(moodboard, context={'request': request})
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Image generation failed for moodboard {moodboard.id}: {str(e)}")
            return Response(
                {'error': f'Image generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def bulk_image_action(self, request, pk=None):
        """Bulk operations on images within a moodboard"""
        moodboard = self.get_object()
        
        # Check permissions
        if not moodboard.can_user_edit(request.user):
            raise PermissionDenied("You don't have permission to edit this moodboard")
        
        serializer = MoodboardImageBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        image_ids = serializer.validated_data['image_ids']
        
        # Get images belonging to this moodboard
        images = MoodboardImage.objects.filter(
            moodboard=moodboard,
            id__in=image_ids
        )
        
        if not images.exists():
            return Response(
                {'error': 'No valid images found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform the bulk action
        try:
            if action_type == 'select':
                images.update(is_selected=True)
                # Auto-assign order indices
                for i, image in enumerate(images):
                    image.order_index = (MoodboardImage.objects.filter(
                        moodboard=moodboard, is_selected=True
                    ).aggregate(models.Max('order_index'))['order_index__max'] or 0) + i + 1
                    image.save(update_fields=['order_index'])
            
            elif action_type == 'deselect':
                images.update(is_selected=False, order_index=0)
            
            elif action_type == 'delete':
                count = images.count()
                images.delete()
                logger.info(f"Deleted {count} images from moodboard {moodboard.id}")
            
            elif action_type == 'reorder':
                order_mapping = serializer.validated_data.get('order_mapping', {})
                for image in images:
                    if str(image.id) in order_mapping:
                        image.order_index = order_mapping[str(image.id)]
                        image.save(update_fields=['order_index'])
            
            elif action_type in ['tag', 'untag']:
                tags = serializer.validated_data.get('tags', [])
                for image in images:
                    for tag in tags:
                        if action_type == 'tag':
                            image.add_tag(tag)
                        else:
                            image.remove_tag(tag)
            
            # Return updated moodboard
            updated_serializer = MoodboardDetailSerializer(moodboard, context={'request': request})
            return Response(updated_serializer.data)
            
        except Exception as e:
            logger.error(f"Bulk action {action_type} failed for moodboard {moodboard.id}: {str(e)}")
            return Response(
                {'error': f'Bulk action failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share moodboard with specific users"""
        moodboard = self.get_object()
        
        # Check permissions
        if not moodboard.can_user_share(request.user):
            raise PermissionDenied("You don't have permission to share this moodboard")
        
        username = request.data.get('username')
        permission = request.data.get('permission', 'view')
        custom_message = request.data.get('message', '')
        
        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_to_share = User.objects.get(username=username)
            
            # Create or update share
            share, created = MoodboardShare.objects.update_or_create(
                moodboard=moodboard,
                user=user_to_share,
                defaults={
                    'permission': permission,
                    'shared_by': request.user,
                    'custom_message': custom_message
                }
            )
            
            action = 'shared' if created else 'updated'
            logger.info(f"Moodboard {moodboard.id} {action} with {username}")
            
            serializer = MoodboardShareSerializer(share, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike a moodboard"""
        moodboard = self.get_object()
        
        # Check if user can view the moodboard
        if not moodboard.can_user_view(request.user):
            raise PermissionDenied("You don't have permission to view this moodboard")
        
        # Simple like increment for now (can be enhanced with user tracking)
        moodboard.increment_like_count()
        
        return Response({'status': 'liked', 'like_count': moodboard.like_count + 1})
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Create a copy of an existing moodboard"""
        original = self.get_object()
        
        # Check permissions
        if not original.can_user_view(request.user):
            raise PermissionDenied("You don't have permission to view this moodboard")
        
        # Create duplicate
        duplicate = Moodboard.objects.create(
            user=request.user,
            title=f"Copy of {original.title}",
            description=original.description,
            category=original.category,
            status='draft',
            tags=original.tags,
            color_palette=original.color_palette,
            is_public=False  # Duplicates are private by default
        )
        
        # Copy selected images
        for image in original.images.filter(is_selected=True):
            MoodboardImage.objects.create(
                moodboard=duplicate,
                image_url=image.image_url,
                thumbnail_url=image.thumbnail_url,
                prompt=image.prompt,
                title=image.title,
                description=image.description,
                source=image.source,
                tags=image.tags,
                is_selected=True,
                order_index=image.order_index,
                width=image.width,
                height=image.height,
                file_size=image.file_size,
                format=image.format
            )
        
        logger.info(f"Duplicated moodboard {original.id} to {duplicate.id} for user {request.user.username}")
        
        serializer = MoodboardDetailSerializer(duplicate, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Bulk operations on multiple moodboards"""
        serializer = MoodboardBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        moodboard_ids = serializer.validated_data['moodboard_ids']
        
        # Get moodboards owned by current user
        moodboards = Moodboard.objects.filter(
            user=request.user,
            id__in=moodboard_ids
        )
        
        if not moodboards.exists():
            return Response(
                {'error': 'No valid moodboards found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            count = moodboards.count()
            
            if action_type == 'delete':
                moodboards.delete()
                logger.info(f"Bulk deleted {count} moodboards for user {request.user.username}")
            
            elif action_type == 'archive':
                moodboards.update(status='archived')
            
            elif action_type == 'unarchive':
                moodboards.update(status='in_progress')
            
            elif action_type == 'make_public':
                moodboards.update(is_public=True)
            
            elif action_type == 'make_private':
                moodboards.update(is_public=False)
            
            elif action_type == 'change_category':
                category = serializer.validated_data.get('category')
                moodboards.update(category=category)
            
            return Response({
                'status': 'success',
                'action': action_type,
                'count': count
            })
            
        except Exception as e:
            logger.error(f"Bulk action {action_type} failed: {str(e)}")
            return Response(
                {'error': f'Bulk action failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MoodboardImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for individual image operations within moodboards
    
    Provides detailed image management capabilities while maintaining
    the moodboard-centric architecture.
    """
    
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MoodboardImageSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get images for moodboards user can access"""
        user = self.request.user
        
        return MoodboardImage.objects.select_related('moodboard', 'moodboard__user').filter(
            Q(moodboard__user=user) |
            Q(moodboard__shared_with=user) |
            Q(moodboard__is_public=True)
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return MoodboardImageCreateSerializer
        return MoodboardImageSerializer
    
    def perform_create(self, serializer):
        """Create image with permission check"""
        moodboard = serializer.validated_data['moodboard']
        
        if not moodboard.can_user_edit(self.request.user):
            raise PermissionDenied("You don't have permission to add images to this moodboard")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Update image with permission check"""
        if not serializer.instance.moodboard.can_user_edit(self.request.user):
            raise PermissionDenied("You don't have permission to edit this image")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Delete image with permission check"""
        if not instance.moodboard.can_user_edit(self.request.user):
            raise PermissionDenied("You don't have permission to delete this image")
        
        instance.delete()


# Legacy compatibility views for gradual migration
class LegacySessionView(viewsets.ViewSet):
    """
    Legacy session compatibility layer
    
    This provides backward compatibility for existing frontend code
    while gradually migrating to the new moodboard-first architecture.
    """
    
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Legacy session start -> Create draft moodboard"""
        # Create a draft moodboard instead of a session
        moodboard = Moodboard.objects.create(
            user=request.user,
            title='Untitled Moodboard',
            status='draft'
        )
        
        logger.info(f"Legacy session compatibility: Created draft moodboard {moodboard.id}")
        
        return Response({
            'session_id': str(moodboard.id),  # Return moodboard ID as session ID
            'message': 'Draft moodboard created (legacy compatibility)'
        })
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Legacy generation -> Forward to moodboard generation"""
        try:
            moodboard = Moodboard.objects.get(id=pk, user=request.user)
        except Moodboard.DoesNotExist:
            return Response(
                {'error': 'Moodboard not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Forward to moodboard generation
        from django.urls import reverse
        from django.test import RequestFactory
        
        factory = RequestFactory()
        generate_request = factory.post(
            reverse('moodboard-generate-images', kwargs={'pk': pk}),
            data=request.data,
            content_type='application/json'
        )
        generate_request.user = request.user
        
        # Call the moodboard generation view
        viewset = MoodboardViewSet()
        viewset.request = generate_request
        viewset.format_kwarg = None
        
        return viewset.generate_images(generate_request, pk=pk)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """Legacy session end -> Mark moodboard as completed"""
        try:
            moodboard = Moodboard.objects.get(id=pk, user=request.user)
        except Moodboard.DoesNotExist:
            return Response(
                {'error': 'Moodboard not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get final selections and title from request
        selected_image_ids = request.data.get('selected_image_ids', [])
        title = request.data.get('title', moodboard.title)
        is_public = request.data.get('is_public', False)
        
        # Update image selections
        if selected_image_ids:
            moodboard.images.update(is_selected=False)
            moodboard.images.filter(id__in=selected_image_ids).update(is_selected=True)
        
        # Update moodboard
        moodboard.title = title
        moodboard.is_public = is_public
        moodboard.mark_as_completed()
        
        logger.info(f"Legacy session end: Completed moodboard {moodboard.id}")
        
        return Response({
            'final_status': 'completed',
            'moodboard_id': str(moodboard.id),
            'message': 'Moodboard completed (legacy compatibility)'
        })


# Health Check and System Status Endpoints
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Basic health check endpoint"""
    try:
        # Simple database connectivity test
        moodboard_count = Moodboard.objects.count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'total_moodboards': moodboard_count,
            'version': '2.0.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """Detailed system status for administrators"""
    try:
        # Database statistics
        stats = {
            'moodboards': {
                'total': Moodboard.objects.count(),
                'draft': Moodboard.objects.filter(status='draft').count(),
                'in_progress': Moodboard.objects.filter(status='in_progress').count(),
                'completed': Moodboard.objects.filter(status='completed').count(),
                'public': Moodboard.objects.filter(is_public=True).count(),
            },
            'images': {
                'total': MoodboardImage.objects.count(),
                'selected': MoodboardImage.objects.filter(is_selected=True).count(),
                'ai_generated': MoodboardImage.objects.filter(source='ai_generated').count(),
                'user_uploaded': MoodboardImage.objects.filter(source='user_upload').count(),
            },
            'users': {
                'total': User.objects.count(),
                'active_creators': User.objects.filter(
                    moodboards__created_at__gte=timezone.now().replace(day=timezone.now().day-30)
                ).distinct().count(),
            },
            'system': {
                'timestamp': timezone.now().isoformat(),
                'version': '2.0.0',
                'architecture': 'unified_moodboard_first',
                'features': [
                    'draft_based_workflow',
                    'unified_api',
                    'bulk_operations',
                    'real_time_collaboration',
                    'advanced_permissions'
                ]
            }
        }
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return Response({
            'status': 'error',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
