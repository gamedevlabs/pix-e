"""
Views for the game_concept app.
"""

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import GameConcept
from .serializers import (
    GameConceptCreateSerializer,
    GameConceptListSerializer,
    GameConceptSerializer,
)


class GameConceptViewSet(ModelViewSet):
    """
    ViewSet for managing game concepts.

    Endpoints:
    - GET /api/game-concept/ - List all concepts for the user
    - GET /api/game-concept/current/ - Get current concept
    - GET /api/game-concept/history/ - Get concept history
    - POST /api/game-concept/ - Create new concept
    - GET /api/game-concept/{id}/ - Get specific concept
    - PUT/PATCH /api/game-concept/{id}/ - Update concept
    - DELETE /api/game-concept/{id}/ - Delete concept
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return concepts for the current user."""
        return GameConcept.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return GameConceptCreateSerializer
        elif self.action == "list" or self.action == "history":
            return GameConceptListSerializer
        return GameConceptSerializer

    def perform_create(self, serializer):
        """Create a new game concept with user from request."""
        serializer.save()

    @action(detail=False, methods=["get"])
    def current(self, request):
        """
        Get the current game concept for the user.

        Returns 404 if no current concept exists.
        """
        try:
            concept = GameConcept.objects.get(user=request.user, is_current=True)
            serializer = GameConceptSerializer(concept)
            return Response(serializer.data)
        except GameConcept.DoesNotExist:
            return Response(
                {"detail": "No current game concept found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def history(self, request):
        """
        Get all past game concepts for the user (including current).

        Returns list ordered by most recent first.
        Uses full serializer to include complete content.
        """
        concepts = GameConcept.objects.filter(user=request.user).order_by("-updated_at")

        serializer = GameConceptSerializer(concepts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_current(self, request):
        """
        Update or create the current game concept.

        Marks all existing concepts as not current and creates
        a new current concept with the provided content.
        """
        content = request.data.get("content")
        if not content:
            return Response(
                {"error": "Content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark all existing concepts as not current
        GameConcept.objects.filter(user=request.user, is_current=True).update(
            is_current=False
        )

        # Create new current concept
        concept = GameConcept.objects.create(
            user=request.user, content=content, is_current=True
        )

        serializer = GameConceptSerializer(concept)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """
        Restore a past game concept as the current one.

        Marks all existing concepts as not current and sets
        the specified concept as current.
        """
        try:
            concept = GameConcept.objects.get(pk=pk, user=request.user)
        except GameConcept.DoesNotExist:
            return Response(
                {"error": "Game concept not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mark all existing concepts as not current
        GameConcept.objects.filter(user=request.user, is_current=True).update(
            is_current=False
        )

        # Set selected concept as current
        concept.is_current = True
        concept.save()

        serializer = GameConceptSerializer(concept)
        return Response(serializer.data)
