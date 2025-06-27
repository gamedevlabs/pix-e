from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import PxComponent, PxComponentDefinition, PxNode
from .serializers import (
    PxComponentDefinitionSerializer,
    PxComponentSerializer,
    PxNodeSerializer,
)


class PxNodeViewSet(viewsets.ModelViewSet):
    serializer_class = PxNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            PxNode.objects.all().filter(owner=self.request.user).order_by("created_at")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    """


class PxComponentDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentDefinitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PxComponentDefinition.objects.filter(owner=self.request.user).order_by(
            "created_at"
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PxComponentViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PxComponent.objects.filter(owner=self.request.user).order_by(
            "created_at"
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
