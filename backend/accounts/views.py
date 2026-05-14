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
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from accounts.constants import PROVIDER_DEFAULT_BASE_URLS
from accounts.serializers import UserSerializer

from .encryption import (
    clear_key_from_session,
    decrypt_api_key,
    derive_encryption_key,
    generate_encryption_salt,
    get_encryption_key_from_session,
    store_key_in_session,
)
from .models import UserApiKey, UserSalt
from .serializers import UserApiKeySerializer
from .throttling import ApiKeyTestRateThrottle

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
        password = request.data.get("password", "")
        user = authenticate(
            username=request.data.get("username", ""), password=password
        )
        if user:
            login(request, user)
            salt_obj, _ = UserSalt.objects.get_or_create(
                user=user,
                defaults={"salt": generate_encryption_salt()},
            )
            key = derive_encryption_key(password, salt=bytes(salt_obj.salt))
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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
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

        try:
            salt_obj = user.encryption_salt
        except UserSalt.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Encryption salt not found. "
                        "Log out and log in again to initialize your encryption salt."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        key = derive_encryption_key(password, salt=bytes(salt_obj.salt))
        store_key_in_session(request.session, key)
        return Response({"status": "ok"})


class ApiKeyViewSet(viewsets.ModelViewSet):
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
        api_key_record = self.get_object()

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
                {"error": "Failed to decrypt key"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        from .validation import validate_key_format

        is_valid, error_msg = validate_key_format(api_key_record.provider, raw_key)
        if not is_valid:
            return Response(
                {"status": "error", "detail": error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        effective_base_url = api_key_record.base_url or PROVIDER_DEFAULT_BASE_URLS.get(
            api_key_record.provider, ""
        )
        success, message = test_provider_connection(
            provider=api_key_record.provider,
            api_key=raw_key,
            base_url=effective_base_url,
        )

        if not success and should_auto_disable(message):
            api_key_record.is_active = False
            api_key_record.disabled_reason = "auth_failure"
            api_key_record.save(update_fields=["is_active", "disabled_reason"])
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

    @action(
        detail=False,
        methods=["GET"],
        url_path="models",
        throttle_classes=[UserRateThrottle],
    )
    def list_models(self, request):
        api_keys = self.get_queryset().filter(is_active=True)
        result = []

        enc_key = get_encryption_key_from_session(request.session)
        if not enc_key:
            return Response(
                {"error": "Encryption key expired. Re-enter your password."},
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
            models = _list_models_for_key(
                key_record.provider, raw_key, effective_base_url
            )
            model_entries = [
                {"name": m.name, "provider": m.provider, "type": m.type} for m in models
            ]

            result.append(
                {
                    "id": str(key_record.id),
                    "label": key_record.label,
                    "provider": key_record.provider,
                    "models": model_entries,
                }
            )

        return Response({"keys": result})


AUTH_FAILURE_PATTERNS = [
    r"\b401\b",
    r"\b403\b",
    "http 401",
    "http 403",
    "status 401",
    "status 403",
    "401 unauthorized",
    "403 forbidden",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "authentication failed",
    "permission denied",
    "not authorized",
    "auth error",
    "invalid authentication credentials",
    "api key not found",
    "credential",
]
_AUTH_FAILURE_REGEX = [re.compile(p, re.IGNORECASE) for p in AUTH_FAILURE_PATTERNS]


def should_auto_disable(error_message: str) -> bool:
    return any(patt.search(error_message) for patt in _AUTH_FAILURE_REGEX)


def sanitize_error_message(error_msg: str, api_key: str) -> str:
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
    try:
        if provider in ("openai", "custom", "morpheus"):
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url=base_url or None,
                timeout=15,
            )
            models = client.models.list()
            first_model = next((m.id for m in models if m.id), "gpt-4o-mini")
            client.chat.completions.create(
                model=first_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True, "Connected successfully."

        elif provider == "gemini":
            from google import genai

            gemini_client = genai.Client(api_key=api_key)
            gemini_models = list(gemini_client.models.list())
            first_model = next(
                (m.name for m in gemini_models if m.name and "/" not in m.name),
                "gemini-2.0-flash-exp",
            )
            gemini_client.models.generate_content(
                model=first_model,
                contents="test",
                config={"max_output_tokens": 1},
            )
            return True, "Connected to Gemini API."

        else:
            return False, f"Unknown provider: {provider}"

    except Exception as e:
        error_msg = sanitize_error_message(str(e), api_key)
        return False, error_msg


def _list_models_for_key(provider: str, api_key: str, base_url: str = ""):
    try:
        if provider in ("openai", "custom", "morpheus"):
            from openai import OpenAI

            from llm.types import ModelCapabilities, ModelDetails

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

            provider_instance = GeminiProvider(
                {
                    "api_key": api_key,
                    "timeout": 10,
                }
            )
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
