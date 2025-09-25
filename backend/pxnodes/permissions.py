from rest_framework import permissions


class IsOwnerPermission(permissions.BasePermission):
    """
    Object-level permission to only allow owners to access or modify their own objects.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
