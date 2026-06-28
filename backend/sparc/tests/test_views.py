"""
Tests for SPARC API views.

Tests both agentic (quick scan) and monolithic view endpoints.
Updated for Split 3: views now use UserLLMOrchestratorMixin and IsAuthenticated.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class TestSPARCQuickScanView:
    """Test SPARCQuickScanView API endpoint."""

    @pytest.mark.django_db
    def test_rejects_missing_game_text(self):
        """Test that endpoint rejects requests without game_text."""
        client = APIClient()
        user = User.objects.create(username="testuser")
        client.force_authenticate(user=user)
        url = reverse("sparc:quick-scan")

        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()
        assert "game_text" in response.json()["error"]

    @pytest.mark.django_db
    def test_rejects_empty_game_text(self):
        """Test that endpoint rejects requests with empty game_text."""
        client = APIClient()
        user = User.objects.create(username="testuser2")
        client.force_authenticate(user=user)
        url = reverse("sparc:quick-scan")

        response = client.post(url, {"game_text": ""}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    @pytest.mark.django_db
    @patch("sparc.views.UserLLMOrchestratorMixin.get_llm_orchestrator")
    def test_accepts_valid_request(self, mock_get_orchestrator):
        """Test that endpoint accepts valid requests and returns results."""
        client = APIClient()
        user = User.objects.create(username="testuser3")
        client.force_authenticate(user=user)
        url = reverse("sparc:quick-scan")

        # Mock successful orchestrator response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.results = {
            "readiness_score": 75,
            "readiness_status": "Nearly Ready",
            "aspect_scores": [],
        }

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_response
        mock_get_orchestrator.return_value = mock_orchestrator

        game_text = "A roguelike dungeon crawler with procedural generation"
        response = client.post(
            url, {"game_text": game_text, "model": "gemini"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "readiness_score" in result
        assert result["readiness_score"] == 75

        # Verify orchestrator was called correctly
        call_args = mock_orchestrator.execute.call_args[0][0]
        assert call_args.feature == "sparc"
        assert call_args.operation == "quick_scan"
        assert call_args.data["game_text"] == game_text

    @pytest.mark.django_db
    @patch("sparc.views.UserLLMOrchestratorMixin.get_llm_orchestrator")
    def test_handles_orchestrator_failure(self, mock_get_orchestrator):
        """Test that endpoint handles orchestrator failures gracefully."""
        client = APIClient()
        user = User.objects.create(username="testuser4")
        client.force_authenticate(user=user)
        url = reverse("sparc:quick-scan")

        # Mock failed orchestrator response
        mock_response = MagicMock()
        mock_response.success = False
        mock_error = MagicMock()
        mock_error.message = "Test error message"
        mock_response.errors = [mock_error]

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_response
        mock_get_orchestrator.return_value = mock_orchestrator

        response = client.post(url, {"game_text": "Test game"}, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in response.json()


class TestSPARCMonolithicView:
    """Test SPARCMonolithicView API endpoint."""

    @pytest.mark.django_db
    def test_rejects_missing_game_text(self):
        """Test that endpoint rejects requests without game_text."""
        client = APIClient()
        user = User.objects.create(username="testuser5")
        client.force_authenticate(user=user)
        url = reverse("sparc:monolithic")

        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()
        assert "game_text" in response.json()["error"]

    @pytest.mark.django_db
    def test_rejects_empty_game_text(self):
        """Test that endpoint rejects requests with empty game_text."""
        client = APIClient()
        user = User.objects.create(username="testuser6")
        client.force_authenticate(user=user)
        url = reverse("sparc:monolithic")

        response = client.post(url, {"game_text": ""}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    @pytest.mark.django_db
    @patch("sparc.views.UserLLMOrchestratorMixin.get_llm_orchestrator")
    def test_accepts_valid_request(self, mock_get_orchestrator):
        """Test that endpoint accepts valid requests and returns results."""
        client = APIClient()
        user = User.objects.create(username="testuser7")
        client.force_authenticate(user=user)
        url = reverse("sparc:monolithic")

        # Mock successful orchestrator response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.results = {
            "overall_assessment": "Good concept",
            "readiness_verdict": "Ready to start development",
        }

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_response
        mock_get_orchestrator.return_value = mock_orchestrator

        game_text = "A roguelike dungeon crawler with procedural generation"
        response = client.post(
            url, {"game_text": game_text, "model": "gemini"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "overall_assessment" in result
        assert result["overall_assessment"] == "Good concept"

        # Verify orchestrator was called correctly
        call_args = mock_orchestrator.execute.call_args[0][0]
        assert call_args.feature == "sparc"
        assert call_args.operation == "monolithic"
        assert call_args.data["game_text"] == game_text

    @pytest.mark.django_db
    @patch("sparc.views.UserLLMOrchestratorMixin.get_llm_orchestrator")
    def test_handles_orchestrator_failure(self, mock_get_orchestrator):
        """Test that endpoint handles orchestrator failures gracefully."""
        client = APIClient()
        user = User.objects.create(username="testuser8")
        client.force_authenticate(user=user)
        url = reverse("sparc:monolithic")

        # Mock failed orchestrator response
        mock_response = MagicMock()
        mock_response.success = False
        mock_error = MagicMock()
        mock_error.message = "Test error message"
        mock_response.errors = [mock_error]

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = mock_response
        mock_get_orchestrator.return_value = mock_orchestrator

        response = client.post(url, {"game_text": "Test game"}, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in response.json()
