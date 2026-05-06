"""Views for the accounts app — authentication and personal API-key management.

Provides user registration, login/logout, session-key re-establishment, and
the personal API-keys feature (CRUD, testing, model listing) with encryption
at rest and session-scoped decryption keys.
"""

import logging
import re

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.timezone import now
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.constants import PROVIDER_DEFAULT_BASE_URLS
from accounts.serializers import UserSerializer

from .encryption import decrypt_api_key, get_encryption_key_from_session, store_key_in_session, clear_key_from_session
from .models import UserApiKey
from .serializers import UserApiKeySerializer
from .throttling import ApiKeyTestRateThrottle
from rest_framework.throttling import UserRateThrottle

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"id": user.id}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, request):
        from .encryption import derive_encryption_key

        password = request.data.get("password", "")
        user = authenticate(
            username=request.data.get("username", ""), password=password
        )
        if user:
            login(request, user)
            # Derive encryption key from plaintext password and store in session
            # with independent 1-hour TTL. This key expires separately from the
            # Django session — the user stays logged in but must re-enter their
            # password to use API key features after 1 hour.
            key = derive_encryption_key(password)
            store_key_in_session(request.session, key)
            return Response({"id": user.id})
        return Response({"error": "Invalid credentials"}, status=400)


class LogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            clear_key_from_session(request.session)
            logout(request)
            return Response({"message": "Logged out successfully"})
        return Response({"error": "User not authenticated"}, status=401)


class MeView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return JsonResponse(
                {"id": request.user.id, "username": request.user.username}
            )
        else:
            return JsonResponse({"error": "User not authenticated"}, status=401)


class ReestablishKeyView(APIView):
    """
    Re-establish the encryption key in the session when it has expired.

    The user's password is required to re-derive the Fernet key.
    This does NOT create a new Django session — it only refreshes the key
    within the existing session.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .encryption import derive_encryption_key

        password = request.data.get("password", "")
        if not password:
            return Response(
                {"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if not user.check_password(password):
            return Response(
                {"error": "Wrong password"}, status=status.HTTP_403_FORBIDDEN
            )

        store_key_in_session(request.session, derive_encryption_key(password))
        return Response({"status": "ok"})


class ApiKeyViewSet(viewsets.ModelViewSet):
    """
    CRUD for user API keys.

    - List: Returns masked keys only (never the raw key)
    - Create: Accepts raw key, encrypts it before storing
    - Retrieve: Never exposes raw key — use /test/ to verify
    - Update: Only metadata (label, is_active), not the key itself
    - Destroy: Permanently deletes the key
    """

    serializer_class = UserApiKeySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserApiKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(
        detail=True,
        methods=["POST"],
        url_path="test",
        throttle_classes=[ApiKeyTestRateThrottle],
    )
    def test_key(self, request, pk=None):
        """
        Test an API key by making a lightweight API call.

        Two-tier validation:
        1. Syntactic: check prefix/length (instant, no network)
        2. Semantic: actual API call to provider (rate-limited)
        """
        api_key_record = self.get_object()

        # Decrypt and do format check
        enc_key = get_encryption_key_from_session(request.session)
        if not enc_key:
            return Response(
                {"error": "Session expired. Please log in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            raw_key = decrypt_api_key(api_key_record.encrypted_key, enc_key)
        except Exception as e:
            logger.error(f"Failed to decrypt key {api_key_record.id}: {e}")
            return Response(
                {"error": "Failed to decrypt key — may need re-encryption"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        from .validation import validate_key_format

        is_valid, error_msg = validate_key_format(api_key_record.provider, raw_key)
        if not is_valid:
            return Response(
                {"status": "error", "detail": error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tier 2: Semantic validation (API call)
        effective_base_url = api_key_record.base_url or PROVIDER_DEFAULT_BASE_URLS.get(
            api_key_record.provider, ""
        )
        success, message = test_provider_connection(
            provider=api_key_record.provider,
            api_key=raw_key,
            base_url=effective_base_url,
        )

        # Auto-disable key on provider auth failure
        if not success and should_auto_disable(message):
            api_key_record.is_active = False
            api_key_record.save(update_fields=["is_active"])
            logger.warning(
                "API key auto-disabled: user=%s id=%s provider=%s",
                request.user.id,
                api_key_record.id,
                api_key_record.provider,
            )
            return Response(
                {
                    "status": "error",
                    "detail": "Key rejected by provider. It has been disabled.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if success:
            api_key_record.last_used_at = now()
            api_key_record.save(update_fields=["last_used_at"])
            return Response({"status": "ok", "detail": message})
        else:
            return Response(
                {"status": "error", "detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(detail=False, methods=["GET"], url_path="models", throttle_classes=[UserRateThrottle])
    def list_models(self, request):
        """
        List all available models from user's active API keys.

        For each active key, decrypts it, creates a provider, and calls
        list_models() to return the actual available models from the API.
        """
        api_keys = self.get_queryset().filter(is_active=True)
        result = []

        enc_key = get_encryption_key_from_session(request.session)
        if not enc_key:
            # User is logged in but encryption key TTL expired.
            # Return 401 — frontend shows password modal.
            return Response(
                {"error": "Encryption key expired. Enter your password to re-enable API key access."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        for key_record in api_keys:
            try:
                raw_key = decrypt_api_key(key_record.encrypted_key, enc_key)
            except Exception:
                continue

            effective_base_url = key_record.base_url or PROVIDER_DEFAULT_BASE_URLS.get(
                key_record.provider, ""
            )
            models = _list_models_for_key(key_record.provider, raw_key, effective_base_url)
            model_entries = [
                {"name": m.name, "provider": m.provider, "type": m.type}
                for m in models
            ]

            # Always include the key entry even with empty models (key exists, just no models)
            result.append({
                "id": str(key_record.id),
                "label": key_record.label,
                "provider": key_record.provider,
                "models": model_entries,
            })

        return Response({"keys": result})


# === Key test & sanitization utilities ===

AUTH_FAILURE_KEYWORDS = [
    "401",
    "403",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "authentication failed",
    "permission denied",
    "not authorized",
    "auth error",
]


def should_auto_disable(error_message: str) -> bool:
    """Determine whether an API key should be auto-disabled based on a provider error.

    Scans the error message for authentication-failure keywords (e.g.
    ``"401"``, ``"unauthorized"``, ``"invalid api key"``). A match means
    the provider definitively rejected the key, so it should be disabled
    to prevent repeated failed calls.

    Args:
        error_message: The raw error string returned by the provider SDK.

    Returns:
        ``True`` if the error contains an auth-failure keyword and the key
        should be disabled; ``False`` otherwise.
    """
    msg = error_message.lower()
    return any(kw in msg for kw in AUTH_FAILURE_KEYWORDS)


def sanitize_error_message(error_msg: str, api_key: str) -> str:
    """Remove sensitive API-key material from an error message.

    Searches for the full key (case-insensitive) and a truncated
    ``prefix...suffix`` pattern (first 8 + last 4 characters) and replaces
    each occurrence with ``"***"``. This prevents keys from leaking into
    logs or API responses.

    Args:
        error_msg: The original error string that may contain the raw key.
        api_key: The full API key to redact. If empty or ``None``, the
            message is returned unchanged.

    Returns:
        The sanitized error string with all occurrences of *api_key*
        replaced by ``"***"``.
    """
    if not api_key or not error_msg:
        return error_msg
    pattern = re.escape(api_key)
    error_msg = re.sub(pattern, "***", error_msg, flags=re.IGNORECASE)
    if len(api_key) >= 12:
        prefix = re.escape(api_key[:8])
        suffix = re.escape(api_key[-4:])
        truncated_pattern = prefix + r".*?" + suffix
        error_msg = re.sub(truncated_pattern, "***", error_msg, flags=re.IGNORECASE)
    return error_msg


def test_provider_connection(provider: str, api_key: str, base_url: str = "") -> tuple:
    """Verify an API key by making a lightweight call to the provider.

    Dispatches to the appropriate SDK (OpenAI or Gemini) based on
    *provider*. For OpenAI-compatible providers (``openai``, ``custom``,
    ``morpheus``) it calls ``client.models.list()``; for ``gemini`` it
    calls ``client.models.list()`` via the Google Generative AI SDK.

    Args:
        provider: Provider identifier (``"openai"``, ``"gemini"``,
            ``"custom"``, or ``"morpheus"``).
        api_key: The raw (decrypted) API key to test.
        base_url: Optional custom base URL for OpenAI-compatible providers.
            Defaults to ``""`` (uses the SDK default).

    Returns:
        A ``(success, message)`` tuple:
        - ``(True, "Connected successfully.")`` or
          ``(True, "Connected to Gemini API.")`` on success.
        - ``(False, <sanitized_error_message>)`` on failure, where the
          error has been stripped of the raw API key.

    Raises:
        (Catches all exceptions internally; does not raise.)
    """
    try:
        if provider in ("openai", "custom", "morpheus"):
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url=base_url or None,
                timeout=10,
            )
            client.models.list()
            return True, "Connected successfully."

        elif provider == "gemini":
            from google import genai

            client = genai.Client(api_key=api_key)
            list(client.models.list())
            return True, "Connected to Gemini API."

        else:
            return False, f"Unknown provider: {provider}"

    except Exception as e:
        error_msg = sanitize_error_message(str(e), api_key)
        return False, error_msg


def _list_models_for_key(provider: str, api_key: str, base_url: str = ""):
    """
    List available models for a provider using given credentials.

    For OpenAI-compatible providers, queries the /v1/models endpoint directly
    via the OpenAI SDK WITHOUT the GPT-only prefix filter — returns ALL models
    the API exposes (needed for Morpheus, custom proxies, etc.).

    Returns a list of ModelDetails objects, or empty list on failure.
    """
    try:
        if provider in ("openai", "custom", "morpheus"):
            from llm.types import ModelCapabilities, ModelDetails

            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=10)
            response = client.models.list()
            models = []
            for model in response.data:
                name = model.id
                if not name:
                    continue
                models.append(
                    ModelDetails(
                        name=name,
                        provider=provider,
                        type="cloud",
                        capabilities=ModelCapabilities(),
                    )
                )
            return models

        elif provider == "gemini":
            from llm.providers.gemini_provider import GeminiProvider

            provider_instance = GeminiProvider({
                "api_key": api_key,
                "timeout": 10,
            })
            return provider_instance.list_models()

        else:
            return []

    except Exception:
        logger.warning(
            "Failed to list models for provider=%s",
            provider,
            exc_info=True,
        )
        return []
