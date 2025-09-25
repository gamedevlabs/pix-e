from rest_framework import permissions

from .models import MoodboardShare


class MoodboardPermission(permissions.BasePermission):
    """
    Custom permission for moodboard operations.
    - Owners can do anything with their moodboards
    - Shared users can view/edit based on their permission level
    - Public moodboards can be viewed by anyone
    """

    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        # For public moodboards (retrieve action), allow unauthenticated access
        # The object-level permission will handle the actual access control
        if view.action == "retrieve":
            return True

        # For all other actions, require authentication
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the specific moodboard"""
        # Public moodboards can be accessed/viewed/edited by anybody (even
        # unauthenticated)
        if obj.is_public:
            return True

        # For private moodboards, require authentication
        if not (request.user and request.user.is_authenticated):
            return False

        # Owner has all permissions
        if obj.user == request.user:
            return True

        # Check if user has shared access
        try:
            share = MoodboardShare.objects.get(moodboard=obj, user=request.user)

            # View permission allows safe methods
            if (
                share.permission == "view"
                and request.method in permissions.SAFE_METHODS
            ):
                return True

            # Comment permission allows safe methods + POST comments
            if share.permission == "comment":
                if request.method in permissions.SAFE_METHODS:
                    return True
                if request.method == "POST" and view.action in [
                    "create_comment",
                    "comments",
                ]:
                    return True

            # Edit permission allows most operations except delete
            if share.permission == "edit":
                if request.method != "DELETE" or view.action != "destroy":
                    return True

        except MoodboardShare.DoesNotExist:
            pass

        return False


class CanViewMoodboard(permissions.BasePermission):
    """Permission to check if user can view a moodboard"""

    def has_permission(self, request, view):
        # Allow unauthenticated access for potential public moodboards
        return True

    def has_object_permission(self, request, view, obj):
        # For moodboard images/comments, check the moodboard permission
        if hasattr(obj, "moodboard"):
            moodboard = obj.moodboard
        else:
            moodboard = obj

        # Public moodboards can be viewed by anyone (even unauthenticated)
        if moodboard.is_public:
            return True

        # For private moodboards, require authentication
        if not (request.user and request.user.is_authenticated):
            return False

        # Owner can always view
        if moodboard.user == request.user:
            return True

        # Check shared access
        return MoodboardShare.objects.filter(
            moodboard=moodboard, user=request.user
        ).exists()


class CanEditMoodboard(permissions.BasePermission):
    """Permission to check if user can edit a moodboard"""

    def has_permission(self, request, view):
        # Allow unauthenticated access for potential public moodboards
        return True

    def has_object_permission(self, request, view, obj):
        # For moodboard images/comments, check the moodboard permission
        if hasattr(obj, "moodboard"):
            moodboard = obj.moodboard
        else:
            moodboard = obj

        # Public moodboards can be edited by anybody (even unauthenticated)
        if moodboard.is_public:
            return True

        # For private moodboards, require authentication
        if not (request.user and request.user.is_authenticated):
            return False

        # Owner can always edit
        if moodboard.user == request.user:
            return True

        # Check if user has edit permission through sharing
        try:
            share = MoodboardShare.objects.get(moodboard=moodboard, user=request.user)
            return share.permission in ["edit", "comment"]
        except MoodboardShare.DoesNotExist:
            return False


class CanCommentOnMoodboard(permissions.BasePermission):
    """Permission to check if user can comment on a moodboard"""

    def has_permission(self, request, view):
        # Allow unauthenticated access for potential public moodboards
        return True

    def has_object_permission(self, request, view, obj):
        # For comments, check the moodboard permission
        if hasattr(obj, "moodboard"):
            moodboard = obj.moodboard
        else:
            moodboard = obj

        # Public moodboards allow comments from anyone (even unauthenticated)
        if moodboard.is_public:
            return True

        # For private moodboards, require authentication
        if not (request.user and request.user.is_authenticated):
            return False

        # Owner can always comment
        if moodboard.user == request.user:
            return True

        # Check if user has comment or edit permission through sharing
        try:
            share = MoodboardShare.objects.get(moodboard=moodboard, user=request.user)
            return share.permission in ["comment", "edit"]
        except MoodboardShare.DoesNotExist:
            return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit their content.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        return obj.user == request.user
