"""
Unit tests for SPARC views.

Tests view configuration and request handling without making actual LLM calls.
"""

from unittest.mock import MagicMock, patch

from django.test import RequestFactory
from rest_framework import status

from sparc.views import SPARCMonolithicView, SPARCQuickScanView


def test_quick_scan_view_validation():
    """Test that quick scan view validates input correctly."""
    print("Testing SPARCQuickScanView input validation...\n")

    factory = RequestFactory()

    # Test missing game_text
    request = factory.post(
        "/api/sparc/quick-scan/",
        data={},
        content_type="application/json",
    )
    request.data = {}

    view = SPARCQuickScanView()
    response = view.post(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.content.decode()
    assert "game_text" in response.content.decode()
    print("✅ Correctly rejects missing game_text")

    # Test with valid game_text (mocked orchestrator)
    request = factory.post(
        "/api/sparc/quick-scan/",
        data={"game_text": "Test game"},
        content_type="application/json",
    )
    request.data = {"game_text": "Test game", "model": "gemini"}

    # Mock the orchestrator to avoid actual LLM calls
    with patch("sparc.views.LLMOrchestrator") as MockOrchestrator:
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.results = {"readiness_score": 75, "test": "data"}

        mock_instance = MockOrchestrator.return_value
        mock_instance.execute.return_value = mock_response

        view = SPARCQuickScanView()
        response = view.post(request)

        assert response.status_code == status.HTTP_200_OK
        print("✅ Accepts valid game_text and returns success")

        # Verify execute was called with correct parameters
        call_args = mock_instance.execute.call_args[0][0]
        assert call_args.feature == "sparc"
        assert call_args.operation == "quick_scan"
        assert call_args.data == {"game_text": "Test game"}
        print("✅ Calls orchestrator with correct parameters\n")


def test_monolithic_view_validation():
    """Test that monolithic view validates input correctly."""
    print("Testing SPARCMonolithicView input validation...\n")

    factory = RequestFactory()

    # Test missing game_text
    request = factory.post(
        "/api/sparc/monolithic/",
        data={},
        content_type="application/json",
    )
    request.data = {}

    view = SPARCMonolithicView()
    response = view.post(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.content.decode()
    assert "game_text" in response.content.decode()
    print("✅ Correctly rejects missing game_text")

    # Test with valid game_text (mocked orchestrator)
    request = factory.post(
        "/api/sparc/monolithic/",
        data={"game_text": "Test game"},
        content_type="application/json",
    )
    request.data = {"game_text": "Test game", "model": "gemini"}

    # Mock the orchestrator to avoid actual LLM calls
    with patch("sparc.views.LLMOrchestrator") as MockOrchestrator:
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.results = {"overall_assessment": "Good", "test": "data"}

        mock_instance = MockOrchestrator.return_value
        mock_instance.execute.return_value = mock_response

        view = SPARCMonolithicView()
        response = view.post(request)

        assert response.status_code == status.HTTP_200_OK
        print("✅ Accepts valid game_text and returns success")

        # Verify execute was called with correct parameters
        call_args = mock_instance.execute.call_args[0][0]
        assert call_args.feature == "sparc"
        assert call_args.operation == "monolithic"
        assert call_args.data == {"game_text": "Test game"}
        print("✅ Calls orchestrator with correct parameters\n")


def test_error_handling():
    """Test that views handle orchestrator errors correctly."""
    print("Testing error handling...\n")

    factory = RequestFactory()

    # Test quick scan error handling
    request = factory.post(
        "/api/sparc/quick-scan/",
        data={"game_text": "Test game"},
        content_type="application/json",
    )
    request.data = {"game_text": "Test game"}

    with patch("sparc.views.LLMOrchestrator") as MockOrchestrator:
        mock_response = MagicMock()
        mock_response.success = False
        mock_error = MagicMock()
        mock_error.message = "Test error"
        mock_response.errors = [mock_error]

        mock_instance = MockOrchestrator.return_value
        mock_instance.execute.return_value = mock_response

        view = SPARCQuickScanView()
        response = view.post(request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in response.content.decode()
        print("✅ Handles orchestrator errors correctly\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPARC Views Unit Tests")
    print("=" * 60 + "\n")

    test_quick_scan_view_validation()
    test_monolithic_view_validation()
    test_error_handling()

    print("=" * 60)
    print("✨ All view tests passed!")
    print("=" * 60)
