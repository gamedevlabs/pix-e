from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import PxNode
from .serializers import PxNodeSerializer

class PxNodeViewSet(viewsets.ModelViewSet):
    queryset = PxNode.objects.all().order_by('-created_at')
    serializer_class = PxNodeSerializer

    """permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)"""