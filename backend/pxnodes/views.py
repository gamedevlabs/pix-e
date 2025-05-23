from rest_framework import viewsets

# from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import PxComponent, PxComponentDefinition, PxNode
from .serializers import (
    PxComponentDefinitionSerializer,
    PxComponentSerializer,
    PxNodeSerializer,
)


class PxNodeViewSet(viewsets.ModelViewSet):
    queryset = PxNode.objects.all().order_by("-created_at")
    serializer_class = PxNodeSerializer

    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    """


class PxComponentDefinitionViewSet(viewsets.ModelViewSet):
    queryset = PxComponentDefinition.objects.all().order_by("-created_at")
    serializer_class = PxComponentDefinitionSerializer


class PxComponentViewSet(viewsets.ModelViewSet):
    queryset = PxComponent.objects.all().order_by("-created_at")
    serializer_class = PxComponentSerializer
