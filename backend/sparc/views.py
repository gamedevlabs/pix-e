"""
SPARC API views.

Placeholder views for SPARC evaluation endpoints.
Will be implemented after agents and graphs are ready.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class SPARCQuickScanView(APIView):
    """
    Quick scan evaluation using parallel agentic execution.

    POST /api/sparc/quick-scan/
    Body: {
        "game_text": "...",
        "context": "..." (optional),
        "model_id": "gpt-4o-mini" (optional)
    }
    """

    def post(self, request):
        """Execute quick scan evaluation."""
        return Response(
            {"message": "Quick scan endpoint - coming soon"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class SPARCMonolithicView(APIView):
    """
    Monolithic baseline evaluation for comparison.

    POST /api/sparc/monolithic/
    Body: {
        "game_text": "...",
        "context": "..." (optional),
        "model_id": "gpt-4o-mini" (optional)
    }
    """

    def post(self, request):
        """Execute monolithic evaluation."""
        return Response(
            {"message": "Monolithic endpoint - coming soon"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
