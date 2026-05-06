"""
Mixin for views that need a per-user LLM orchestrator.
"""

from rest_framework.exceptions import NotAuthenticated

from accounts.encryption import get_encryption_key_from_session
from llm import LLMOrchestrator


class UserLLMOrchestratorMixin:
    """
    Provides `get_llm_orchestrator()` that creates a user-scoped orchestrator.

    The user's encryption key (derived from their password at login, stored
    in the session) is extracted and passed to the orchestrator so API keys
    can be decrypted in-memory for the duration of the request.

    If the encryption key is missing (session expired, not logged in),
    raises NotAuthenticated (401) which the frontend catches to show the
    password re-entry modal.
    """

    def get_llm_orchestrator(self, request):
        """
        Create an LLMOrchestrator for the current user.

        Raises NotAuthenticated if the encryption key is missing from the
        session (expired or user never logged in since the feature was added).
        """
        enc_key = get_encryption_key_from_session(request.session)
        if not enc_key:
            raise NotAuthenticated(
                detail="Encryption key expired. Enter your password to re-enable API key access."
            )

        api_key_id = request.data.get("api_key_id") or request.query_params.get(
            "api_key_id"
        )
        if api_key_id:
            return LLMOrchestrator.for_user_and_key(
                request.user, api_key_id, enc_key
            )
        return LLMOrchestrator.for_user(request.user, enc_key)
