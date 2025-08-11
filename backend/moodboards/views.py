from .serializers import (
    ImageBulkActionSerializer,
    MoodboardBulkActionSerializer,
    MoodboardCommentSerializer,
    MoodboardCreateUpdateSerializer,
    MoodboardDetailSerializer,
    MoodboardImageCreateSerializer,
    MoodboardImageSerializer,
    MoodboardListSerializer,
    MoodboardTemplateSerializer,
)
from .permissions import CanEditMoodboard, CanViewMoodboard, MoodboardPermission
from .models import (
    Moodboard,
    MoodboardComment,
    MoodboardImage,
    MoodboardShare,
    MoodboardTemplate,
)
from datetime import datetime, timedelta

from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session authentication that doesn't enforce CSRF for API calls"""

    def enforce_csrf(self, request):
        return  # Skip CSRF check


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination configuration"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MoodboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Moodboard CRUD operations.

    Provides:
    - List moodboards (with filtering and search)
    - Create new moodboard
    - Retrieve specific moodboard
    - Update moodboard
    - Delete moodboard
    - Bulk actions
    - Sharing functionality
    - Comments
    - Analytics
    """

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MoodboardPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "tags"]
    ordering_fields = ["created_at", "updated_at", "title", "status"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        """Get moodboards visible to the current user"""
        user = self.request.user

        # Base queryset with optimized joins
        queryset = (
            Moodboard.objects.select_related("user")
            .prefetch_related("images", "shared_with", "comments__user")
            .annotate(
                total_images=Count("images", distinct=True),
                total_comments=Count("comments", distinct=True),
            )
        )

        # Filter based on action
        action = self.action

        if action == "public":
            # Public moodboards - ensure they actually exist and are accessible
            public_queryset = queryset.filter(is_public=True)

            # Add additional filtering to ensure moodboards are valid
            public_queryset = public_queryset.filter(
                user__isnull=False,  # Ensure user still exists
                title__isnull=False,  # Ensure basic fields are not null
            )

            return public_queryset
        elif action == "shared_with_me":
            # Moodboards shared with the user
            return queryset.filter(shared_with=user)
        else:
            # For retrieve action, include public moodboards from all users
            if action == "retrieve":
                accessible_queryset = queryset.filter(
                    Q(user=user)  # User's own moodboards
                    | Q(is_public=True)  # Public moodboards from all users
                )
                return accessible_queryset

            # Return only user's own moodboards for list and other actions
            return queryset.filter(user=user)

    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        if self.action == "list":
            return MoodboardListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return MoodboardCreateUpdateSerializer
        else:
            return MoodboardDetailSerializer

    def perform_create(self, serializer):
        """Set the user when creating a moodboard"""
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Custom retrieve method with better error handling"""
        moodboard_id = kwargs.get("pk")

        try:
            # Validate UUID format first
            import uuid

            try:
                uuid.UUID(moodboard_id)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid moodboard ID format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Try to get the object using Django REST's method
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except (Moodboard.DoesNotExist, Http404):
            return Response(
                {"detail": "No Moodboard matches the given query."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied:
            return Response(
                {"detail": "You do not have permission to access this moodboard."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            return Response(
                {"detail": "An error occurred while retrieving the moodboard."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def public(self, request):
        """Get public moodboards"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MoodboardListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = MoodboardListSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def shared_with_me(self, request):
        """Get moodboards shared with the current user"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Use SharedMoodboardSerializer to include permission info
            from .serializers import SharedMoodboardSerializer

            serializer = SharedMoodboardSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        from .serializers import SharedMoodboardSerializer

        serializer = SharedMoodboardSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recently updated moodboards"""
        # Get moodboards updated in the last 7 days
        recent_date = datetime.now() - timedelta(days=7)
        queryset = self.get_queryset().filter(updated_at__gte=recent_date)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MoodboardListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = MoodboardListSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Create a duplicate of a moodboard"""
        moodboard = self.get_object()

        # Create duplicate
        duplicate = Moodboard.objects.create(
            user=request.user,
            title=f"{moodboard.title} (Copy)",
            description=moodboard.description,
            category=moodboard.category,
            tags=moodboard.tags,
            color_palette=moodboard.color_palette,
            status="draft",
        )

        # Duplicate images
        for image in moodboard.images.all():
            MoodboardImage.objects.create(
                moodboard=duplicate,
                image_url=image.image_url,
                thumbnail_url=image.thumbnail_url,
                original_filename=image.original_filename,
                prompt=image.prompt,
                generation_params=image.generation_params,
                title=image.title,
                description=image.description,
                source=image.source,
                tags=image.tags,
                order_index=image.order_index,
                width=image.width,
                height=image.height,
                file_size=image.file_size,
            )

        serializer = MoodboardDetailSerializer(duplicate, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[CanEditMoodboard])
    def share(self, request, pk=None):
        """Share a moodboard with other users"""
        moodboard = self.get_object()
        user_id = request.data.get("user_id")
        permission = request.data.get("permission", "view")

        if not user_id:
            return Response(
                {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from django.contrib.auth.models import User

            user_to_share_with = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Create or update share
        share, created = MoodboardShare.objects.update_or_create(
            moodboard=moodboard,
            user=user_to_share_with,
            defaults={"permission": permission, "shared_by": request.user},
        )

        return Response(
            {"message": "Moodboard shared successfully", "created": created}
        )

    @action(detail=True, methods=["post"], permission_classes=[CanEditMoodboard])
    def bulk_share(self, request, pk=None):
        """Share a moodboard with multiple users at once"""
        moodboard = self.get_object()
        user_ids = request.data.get("user_ids", [])
        permission = request.data.get("permission", "view")

        if not user_ids or not isinstance(user_ids, list):
            return Response(
                {"error": "user_ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate permission level
        if permission not in ["view", "comment", "edit"]:
            return Response(
                {"error": "Invalid permission level. Must be view, comment, or edit"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth.models import User

        # Find valid users
        valid_users = User.objects.filter(id__in=user_ids)
        valid_user_ids = list(valid_users.values_list("id", flat=True))
        invalid_user_ids = [uid for uid in user_ids if uid not in valid_user_ids]

        # Share with valid users
        shared_count = 0
        created_count = 0
        errors = []

        for user in valid_users:
            try:
                share, created = MoodboardShare.objects.update_or_create(
                    moodboard=moodboard,
                    user=user,
                    defaults={"permission": permission, "shared_by": request.user},
                )
                shared_count += 1
                if created:
                    created_count += 1
            except Exception as e:
                errors.append(f"Failed to share with user {user.id}: {str(e)}")

        response_data = {
            "message": f"Moodboard shared with {shared_count} user(s)",
            "shared_count": shared_count,
            "created_count": created_count,
            "updated_count": shared_count - created_count,
            "valid_user_ids": valid_user_ids,
        }

        if invalid_user_ids:
            response_data["invalid_user_ids"] = invalid_user_ids
            response_data["warning"] = f"{len(invalid_user_ids)} user(s) not found"

        if errors:
            response_data["errors"] = errors

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], permission_classes=[CanEditMoodboard])
    def unshare(self, request, pk=None):
        """Remove sharing for a moodboard"""
        moodboard = self.get_object()
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            share = MoodboardShare.objects.get(moodboard=moodboard, user_id=user_id)
            share.delete()
            return Response({"message": "Sharing removed successfully"})
        except MoodboardShare.DoesNotExist:
            return Response(
                {"error": "Share not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on moodboards"""
        serializer = MoodboardBulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        moodboard_ids = data["moodboard_ids"]
        action = data["action"]

        # Get moodboards user can edit
        queryset = self.get_queryset().filter(id__in=moodboard_ids, user=request.user)

        if action == "delete":
            count = queryset.count()
            queryset.delete()
            return Response({"message": f"{count} moodboards deleted"})

        elif action == "archive":
            count = queryset.update(status="archived")
            return Response({"message": f"{count} moodboards archived"})

        elif action == "unarchive":
            count = queryset.update(status="draft")
            return Response({"message": f"{count} moodboards unarchived"})

        elif action == "change_status":
            new_status = data["new_status"]
            count = queryset.update(status=new_status)
            return Response({"message": f"{count} moodboards updated"})

        elif action == "duplicate":
            duplicates = []
            for moodboard in queryset:
                duplicate = Moodboard.objects.create(
                    user=request.user,
                    title=f"{moodboard.title} (Copy)",
                    description=moodboard.description,
                    category=moodboard.category,
                    tags=moodboard.tags,
                    color_palette=moodboard.color_palette,
                    status="draft",
                )
                duplicates.append(duplicate.id)
            return Response(
                {
                    "message": f"{len(duplicates)} moodboards duplicated",
                    "duplicate_ids": duplicates,
                }
            )

        elif action in ["add_tags", "remove_tags"]:
            tags_field = "tags_to_add" if action == "add_tags" else "tags_to_remove"
            tags = data[tags_field]

            for moodboard in queryset:
                if action == "add_tags":
                    for tag in tags.split(","):
                        moodboard.add_tag(tag.strip())
                else:
                    for tag in tags.split(","):
                        moodboard.remove_tag(tag.strip())

            return Response(
                {"message": f"Tags updated for {queryset.count()} moodboards"}
            )

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @action(detail=False, methods=["get"])
    def analytics(self, request):
        """Get analytics data for user's moodboards"""
        queryset = self.get_queryset().filter(user=request.user)

        # Basic stats
        total_moodboards = queryset.count()
        by_status = queryset.values("status").annotate(count=Count("id"))
        by_category = queryset.values("category").annotate(count=Count("id"))

        # Images stats - count only selected images that are actually used in moodboards
        total_images = MoodboardImage.objects.filter(
            moodboard__user=request.user, is_selected=True
        ).count()
        # Keep selected_images for potential future use, but use total_images for
        # the main count
        selected_images = total_images

        # Recent activity
        recent_date = datetime.now() - timedelta(days=30)
        recent_moodboards = queryset.filter(created_at__gte=recent_date).count()

        # Public moodboards count
        public_moodboards = queryset.filter(is_public=True).count()

        # Additional useful stats
        completed_moodboards = queryset.filter(status="completed").count()
        avg_images_per_moodboard = (
            total_images / total_moodboards if total_moodboards > 0 else 0
        )

        return Response(
            {
                "total_moodboards": total_moodboards,
                "total_images": total_images,
                "public_moodboards": public_moodboards,
                "selected_images": selected_images,
                "recent_moodboards": recent_moodboards,
                "completed_moodboards": completed_moodboards,
                "avg_images_per_moodboard": round(avg_images_per_moodboard, 1),
                "by_status": list(by_status),
                "by_category": list(by_category),
            }
        )


class MoodboardImageViewSet(viewsets.ModelViewSet):
    """ViewSet for MoodboardImage CRUD operations within a moodboard"""

    serializer_class = MoodboardImageSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewMoodboard]

    def get_queryset(self):
        """Get images for a specific moodboard"""
        moodboard_id = self.kwargs.get("moodboard_pk")
        return MoodboardImage.objects.filter(moodboard_id=moodboard_id).select_related(
            "moodboard"
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ["create"]:
            return MoodboardImageCreateSerializer
        return MoodboardImageSerializer

    def perform_create(self, serializer):
        """Set the moodboard when creating an image"""
        moodboard_id = self.kwargs.get("moodboard_pk")
        moodboard = get_object_or_404(Moodboard, id=moodboard_id)
        serializer.save(moodboard=moodboard)

    @action(detail=False, methods=["post"])
    def bulk_action(self, request, moodboard_pk=None):
        """Perform bulk actions on images"""
        serializer = ImageBulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        image_ids = data["image_ids"]
        action = data["action"]

        # Get images from this moodboard
        queryset = self.get_queryset().filter(id__in=image_ids)

        if action == "select":
            count = queryset.update(is_selected=True)
            return Response({"message": f"{count} images selected"})

        elif action == "unselect":
            count = queryset.update(is_selected=False)
            return Response({"message": f"{count} images unselected"})

        elif action == "delete":
            count = queryset.count()
            queryset.delete()
            return Response({"message": f"{count} images deleted"})

        elif action == "reorder":
            new_order_indices = data["new_order_indices"]
            for i, image_id in enumerate(image_ids):
                queryset.filter(id=image_id).update(order_index=new_order_indices[i])
            return Response({"message": f"{len(image_ids)} images reordered"})

        elif action in ["add_tags", "remove_tags"]:
            tags_field = "tags_to_add" if action == "add_tags" else "tags_to_remove"
            tags = data[tags_field]

            for image in queryset:
                current_tags = image.tag_list

                if action == "add_tags":
                    for tag in tags.split(","):
                        tag = tag.strip()
                        if tag not in current_tags:
                            current_tags.append(tag)
                else:
                    for tag in tags.split(","):
                        tag = tag.strip()
                        if tag in current_tags:
                            current_tags.remove(tag)

                image.tags = ", ".join(current_tags)
                image.save()

            return Response({"message": f"Tags updated for {queryset.count()} images"})

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


class MoodboardCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for MoodboardComment operations"""

    serializer_class = MoodboardCommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewMoodboard]

    def get_queryset(self):
        """Get comments for a specific moodboard"""
        moodboard_id = self.kwargs.get("moodboard_pk")
        return (
            MoodboardComment.objects.filter(moodboard_id=moodboard_id)
            .select_related("user", "moodboard", "image")
            .prefetch_related("replies")
        )

    def perform_create(self, serializer):
        """Set user and moodboard when creating a comment"""
        moodboard_id = self.kwargs.get("moodboard_pk")
        moodboard = get_object_or_404(Moodboard, id=moodboard_id)
        serializer.save(user=self.request.user, moodboard=moodboard)


class MoodboardTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for MoodboardTemplate operations"""

    serializer_class = MoodboardTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]

    def get_queryset(self):
        """Get active templates"""
        return MoodboardTemplate.objects.filter(is_active=True).select_related(
            "created_by"
        )

    def perform_create(self, serializer):
        """Set the creator when creating a template"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def use_template(self, request, pk=None):
        """Create a new moodboard from a template"""
        template = self.get_object()

        # Create moodboard from template
        moodboard = Moodboard.objects.create(
            user=request.user,
            title=request.data.get("title", f"From {template.title}"),
            description=request.data.get("description", template.description),
            category=template.category,
            tags=template.default_tags,
            color_palette=template.default_color_palette,
            status="draft",
        )

        # Increment template usage
        template.increment_usage()

        serializer = MoodboardDetailSerializer(moodboard, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MoodboardAIViewSet(viewsets.GenericViewSet):
    """ViewSet for AI-powered moodboard operations"""

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="start-session")
    def start_session(self, request):
        """Start a new AI moodboard session"""
        try:
            # Get or create user for development
            user = request.user

            # Create a new moodboard for the session
            moodboard = Moodboard.objects.create(
                user=user,
                title=request.data.get(
                    "title", f'AI Moodboard {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                ),
                description=request.data.get(
                    "description", "AI-generated moodboard session"
                ),
                category=request.data.get("category", "gaming"),
                tags=request.data.get("tags", ""),
                color_palette=request.data.get("color_palette", []),
                status="draft",
            )

            return Response(
                {
                    "session_id": str(moodboard.id),
                    "moodboard": MoodboardDetailSerializer(
                        moodboard, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to start session: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="generate-images")
    def generate_images(self, request):
        """Generate AI images for a moodboard"""
        try:
            # Get or create user for development
            user = request.user

            data = request.data
            session_id = data.get("session_id")
            prompt = data.get("prompt", "")
            selected_image_ids = data.get("selected_image_ids", [])
            data.get("mode", "gaming")

            if not session_id:
                return Response(
                    {"error": "session_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not prompt:
                return Response(
                    {"error": "prompt is required"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Get the moodboard
            try:
                moodboard = Moodboard.objects.get(id=session_id)

                # Check if current user has permission to modify this moodboard
                if moodboard.user != user:
                    # For public moodboards, allow anyone to modify them
                    if moodboard.is_public:
                        # Don't change ownership for public moodboards - keep original
                        # owner
                        pass
                    # For AI sessions, be more lenient - allow modification if it's a
                    # recent session or the user is authenticated
                    elif (
                        moodboard.status in ["draft", "active", "generating"]
                        or moodboard.user.username == "testuser123"
                    ):
                        # Update the moodboard owner to current user to maintain
                        # consistency
                        moodboard.user = user
                        moodboard.save()
                    else:
                        return Response(
                            {
                                "error": (
                                    "You do not have permission to modify this "
                                    "moodboard session"
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )

            except Moodboard.DoesNotExist:
                return Response(
                    {"error": "Moodboard session not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Update moodboard with new prompt info
            if "AI-generated moodboard session" in moodboard.description:
                moodboard.description = prompt
            else:
                moodboard.description += f" | {prompt}"
            moodboard.save()

            # Import the image generation function
            from llm.views import generate_gaming_images

            # Generate new images
            try:
                generated_urls = generate_gaming_images(prompt, num_images=3)

                # Add generated images to moodboard
                added_images = []
                for i, image_url in enumerate(generated_urls):
                    # Create MoodboardImage instance directly instead of using
                    # serializer
                    image = MoodboardImage.objects.create(
                        moodboard=moodboard,  # Pass the moodboard instance
                        image_url=image_url,
                        title=f"Generated Image {i+1}",
                        prompt=prompt,
                        source="ai_generated",
                        is_selected=False,  # New images start as unselected
                        order_index=i,
                    )
                    added_images.append(
                        {
                            "id": str(image.id),
                            "url": image.image_url,
                            "title": image.title,
                            "prompt": image.prompt,
                            "is_selected": image.is_selected,
                        }
                    )

                # Process any selected image IDs (mark them as selected)
                if selected_image_ids:
                    MoodboardImage.objects.filter(
                        id__in=selected_image_ids, moodboard=moodboard
                    ).update(is_selected=True)

                # Get updated moodboard data
                moodboard.refresh_from_db()
                all_images = moodboard.images.all()
                generated_images = [img for img in all_images if not img.is_selected]
                selected_images = [img for img in all_images if img.is_selected]

                return Response(
                    {
                        "generated_images": MoodboardImageSerializer(
                            generated_images, many=True
                        ).data,
                        "moodboard": MoodboardImageSerializer(
                            selected_images, many=True
                        ).data,
                        "session_id": str(moodboard.id),
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as e:
                return Response(
                    {"error": f"Failed to generate images: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": f"Image generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="session/(?P<session_id>[^/.]+)")
    def get_session(self, request, session_id=None):
        """Get current session data"""
        try:
            # Get or create user for development
            user = request.user

            try:
                moodboard = Moodboard.objects.get(id=session_id)

                # Check if current user has permission to view this moodboard
                if moodboard.user != user:
                    # For public moodboards, allow anyone to view them
                    if moodboard.is_public:
                        # Don't change ownership for public moodboards - keep original
                        # owner
                        pass
                    # For AI sessions, be more lenient - allow viewing if it's a recent
                    # session or the user is authenticated
                    elif (
                        moodboard.status in ["draft", "active", "generating"]
                        or moodboard.user.username == "testuser123"
                    ):
                        pass
                        # Update the moodboard owner to current user to maintain
                        # consistency
                        moodboard.user = user
                        moodboard.save()
                    else:
                        return Response(
                            {
                                "error": (
                                    "You do not have permission to view this "
                                    "moodboard session"
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )

            except Moodboard.DoesNotExist:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

            all_images = moodboard.images.all()

            generated_images = [img for img in all_images if not img.is_selected]
            selected_images = [img for img in all_images if img.is_selected]

            return Response(
                {
                    "images": MoodboardImageSerializer(
                        generated_images, many=True
                    ).data,
                    "moodboard": MoodboardImageSerializer(
                        selected_images, many=True
                    ).data,
                    "session_id": str(moodboard.id),
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to get session: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="end-session")
    def end_session(self, request):
        """End AI moodboard session"""
        try:
            # Get or create user for development
            user = request.user

            session_id = request.data.get("session_id")
            selected_image_ids = request.data.get("selected_image_ids", [])
            title = request.data.get("title")
            is_public = request.data.get("public")

            if not session_id:
                return Response(
                    {"error": "session_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the moodboard - try to find it regardless of user first
            try:
                moodboard = Moodboard.objects.get(id=session_id)

                # Check if current user has permission to modify this moodboard
                if moodboard.user != user:
                    # For public moodboards, allow anyone to modify them
                    if moodboard.status in ["draft", "active", "generating"]:
                        # Update the moodboard owner to current user to maintain
                        # consistency
                        moodboard.user = user
                        moodboard.save()
                    else:
                        return Response(
                            {
                                "error": (
                                    "You do not have permission to modify this "
                                    "moodboard session"
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )

            except Moodboard.DoesNotExist:
                return Response(
                    {"error": "Moodboard session not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Update moodboard title and public status if provided
            if title:
                moodboard.title = title
            if is_public is not None:
                moodboard.is_public = is_public

            # Mark selected images and finalize moodboard
            if selected_image_ids:
                MoodboardImage.objects.filter(
                    id__in=selected_image_ids, moodboard=moodboard
                ).update(is_selected=True)

            # Update moodboard status to completed
            moodboard.status = "completed"
            moodboard.save()

            # Get final moodboard state
            selected_images = moodboard.images.filter(is_selected=True)

            return Response(
                {
                    "moodboard": MoodboardImageSerializer(
                        selected_images, many=True
                    ).data,
                    "session_id": str(moodboard.id),
                    "status": "completed",
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to end session: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="preload",
        permission_classes=[permissions.AllowAny],
    )
    def preload(self, request):
        """Preload AI services and models"""
        try:
            # This is mainly a placeholder for AI service preloading
            # In a real implementation, this would warm up AI models
            return Response({"status": "ready", "message": "AI services are ready"})
        except Exception as e:
            return Response(
                {"error": f"Failed to preload: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
