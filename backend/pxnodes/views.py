from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import PxComponent, PxComponentDefinition, PxNode
from .permissions import IsOwnerPermission
from .serializers import (
    PxComponentDefinitionSerializer,
    PxComponentSerializer,
    PxNodeSerializer,
)


class PxNodeViewSet(viewsets.ModelViewSet):
    serializer_class = PxNodeSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        if self.action == "list":
            return PxNode.objects.filter(owner=self.request.user)
        return PxNode.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    """


class PxComponentDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentDefinitionSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        if self.action == "list":
            return PxComponentDefinition.objects.filter(owner=self.request.user)
        return PxComponentDefinition.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PxComponentViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        if self.action == "list":
            return PxComponent.objects.filter(owner=self.request.user)
        return PxComponent.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
