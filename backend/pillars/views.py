import logging

from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.exceptions import APIException as _DRFException

from accounts.models import UserApiKey
from accounts.views import should_auto_disable as _should_auto_disable
from llm import get_config
from llm.exceptions import AuthenticationError, OrchestratorError, ProviderError
from llm.mixins import UserLLMOrchestratorMixin
from llm.types import LLMRequest

# Import handlers to trigger auto-registration
from pillars.llm import handlers  # noqa: F401

from .models import GameDesignDescription, Pillar
from .serializers import GameDesignSerializer, PillarSerializer

logger = logging.getLogger(__name__)


# Provider names in error context → UserApiKey.provider values.
# The OpenAI provider class sets provider="openai" in errors, but user keys
# using the same SDK may be stored as "custom" or "morpheus".
_PROVIDER_KEY_MAP: dict[str, list[str]] = {
    "openai": ["openai", "custom", "morpheus"],
    "gemini": ["gemini"],
}


def _disable_keys_for_provider(request, provider: str) -> int:
    """Set is_active=False + disabled_reason for all active keys of a provider."""
    mapped_providers = _PROVIDER_KEY_MAP.get(provider, [provider])
    return UserApiKey.objects.filter(
        user=request.user, provider__in=mapped_providers, is_active=True
    ).update(is_active=False, disabled_reason="auth_failure")


def _handle_orchestrator_error(request, e: Exception) -> JsonResponse:
    """
    Handle LLM orchestrator errors consistently, auto-disabling invalid keys.

    Returns a JsonResponse with an appropriate HTTP status and user-facing
    message instead of a cryptic 500.
    """
    # Extract provider from exception context if available
    provider = ""
    if isinstance(e, AuthenticationError):
        provider = e.context.get("provider", "")
    elif isinstance(e, ProviderError):
        provider = e.context.get("provider", "")
        # Also check the message for auth keywords as fallback
        msg = str(e)
        provider_in_msg = ""
        for p in ["openai", "gemini"]:
            if f"provider '{p}'" in msg.lower():
                provider_in_msg = p
                break
        provider = provider or provider_in_msg

    # Auto-disable if we know the provider and the error looks like auth failure
    if provider and provider != "none":
        is_auth = isinstance(e, AuthenticationError) or (
            isinstance(e, ProviderError) and _should_auto_disable(str(e))
        )
        if is_auth:
            count = _disable_keys_for_provider(request, provider)
            if count:
                logger.warning(
                    "Auto-disabled %d %s API key(s) for user %s: %s",
                    count, provider, request.user.id, str(e)[:120],
                )
            return JsonResponse(
                {
                    "error": "Your API key is invalid and has been disabled. "
                    "Please re-add it in Settings.",
                },
                status=401,
            )

    if isinstance(e, OrchestratorError):
        msg = str(e)
        if "No LLM providers available" in msg:
            return JsonResponse(
                {
                    "error": "No API keys configured. "
                    "Please add an API key in Settings to use AI features.",
                },
                status=400,
            )

    if isinstance(e, _DRFException):
        raise

    logger.exception("Error in LLM operation")
    return JsonResponse({"error": str(e)}, status=500)


def get_model_id(model_name: str) -> str:
    """Map frontend model names to actual model IDs using orchestrator config."""
    config = get_config()
    return config.resolve_model_alias(model_name)


def format_pillars_text(pillars: list[Pillar]) -> str:
    """Format pillars as text for orchestrator."""
    return "\n".join(
        [f"{i+1}. {p.name}: {p.description}" for i, p in enumerate(pillars)]
    )


class PillarViewSet(ModelViewSet):
    serializer_class = PillarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pillar.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DesignView(ModelViewSet):
    serializer_class = GameDesignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GameDesignDescription.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Return the user's game design or raise Http404.

        DRF's ``get_object()`` contract requires raising Http404 on missing
        objects — returning None breaks downstream serializer/DRF machinery.
        """
        try:
            return GameDesignDescription.objects.get(user=self.request.user)
        except GameDesignDescription.DoesNotExist:
            from django.http import Http404
            raise Http404("No game design description found for this user.")

    def get_object_or_404(self):
        """Return design or raise 404 if not found."""
        from django.shortcuts import get_object_or_404 as _get_object_or_404
        return _get_object_or_404(GameDesignDescription, user=self.request.user)

    @action(detail=False, methods=["GET"], url_path="get_or_create")
    def get_or_create(self, request):
        obj, created = GameDesignDescription.objects.get_or_create(
            user=self.request.user, defaults={"description": ""}
        )
        serializer = self.get_serializer(obj)
        return Response(
            serializer.data,
            status=201 if created else 200,
        )


class PillarFeedbackView(UserLLMOrchestratorMixin, ViewSet):
    """View for per-pillar LLM feedback (validate, fix)."""

    @action(detail=True, methods=["POST"], url_path="validate")
    def validate_pillar(self, request, pk):
        try:
            pillar = Pillar.objects.filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            model = request.data.get("model", "gemini")

            # Create orchestrator request
            llm_request = LLMRequest(
                feature="pillars",
                operation="validate",
                data={"name": pillar.name, "description": pillar.description},
                model_id=get_model_id(model),
            )

            # Execute through per-user orchestrator
            response = self.get_llm_orchestrator(request).execute(llm_request)

            return JsonResponse(response.results, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)

    @action(detail=True, methods=["POST"], url_path="fix")
    def fix_pillar(self, request, pk):
        """Fix a pillar using AI suggestions."""
        try:
            pillar = Pillar.objects.filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            model = request.data.get("model", "gemini")

            # Create orchestrator request
            llm_request = LLMRequest(
                feature="pillars",
                operation="improve",
                data={"name": pillar.name, "description": pillar.description},
                model_id=get_model_id(model),
            )

            # Execute through per-user orchestrator
            response = self.get_llm_orchestrator(request).execute(llm_request)

            # Update pillar with improved version
            improved = response.results
            pillar.name = improved.get("name", pillar.name)
            pillar.description = improved.get("description", pillar.description)
            pillar.save()

            # Return serialized pillar
            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)


class LLMFeedbackView(UserLLMOrchestratorMixin, ViewSet):
    """View for overall LLM feedback (completeness, contradictions, additions)."""

    @action(detail=False, methods=["POST"], url_path="overall")
    def overall_feedback(self, request):
        """
        Overall feedback - calls 3 operations sequentially.
        This replicates the old evaluate_pillars_in_context behavior.
        """
        try:
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()
            pillars = list(Pillar.objects.filter(user=request.user))

            if not design:
                return JsonResponse(
                    {"error": "No game design description found"}, status=404
                )

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text = format_pillars_text(pillars)

            completeness_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={"pillars_text": pillars_text, "context": design.description},
                model_id=model_id,
            )
            contradictions_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={"pillars_text": pillars_text, "context": design.description},
                model_id=model_id,
            )
            additions_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={"pillars_text": pillars_text, "context": design.description},
                model_id=model_id,
            )

            # Cache orchestrator — each get_llm_orchestrator() call constructs a
            # new LLMOrchestrator → ModelManager → decrypts all keys → network calls.
            orchestrator = self.get_llm_orchestrator(request)
            completeness_response = orchestrator.execute(completeness_request)
            contradictions_response = orchestrator.execute(contradictions_request)
            additions_response = orchestrator.execute(additions_request)

            combined_result = {
                "coverage": completeness_response.results,
                "contradictions": contradictions_response.results,
                "proposedAdditions": additions_response.results,
            }

            return JsonResponse(combined_result, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)

    @action(detail=False, methods=["POST"], url_path="completeness")
    def completeness(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()

            if not design:
                return JsonResponse(
                    {"error": "No game design description found"}, status=404
                )

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": design.description,
                },
                model_id=get_model_id(model),
            )

            response = self.get_llm_orchestrator(request).execute(llm_request)
            return JsonResponse(response.results, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)

    @action(detail=False, methods=["POST"], url_path="contradictions")
    def contradictions(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()

            if not design:
                return JsonResponse(
                    {"error": "No game design description found"}, status=404
                )

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": design.description,
                },
                model_id=get_model_id(model),
            )

            response = self.get_llm_orchestrator(request).execute(llm_request)
            return JsonResponse(response.results, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)

    @action(detail=False, methods=["POST"], url_path="additions")
    def additions(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()

            if not design:
                return JsonResponse(
                    {"error": "No game design description found"}, status=404
                )

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": design.description,
                },
                model_id=get_model_id(model),
            )

            response = self.get_llm_orchestrator(request).execute(llm_request)
            return JsonResponse(response.results, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)

    @action(detail=False, methods=["POST"], url_path="context")
    def context(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            context_text = request.data.get("context", "")

            if not context_text:
                return JsonResponse({"error": "No context provided"}, status=400)

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_context",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": context_text,
                },
                model_id=get_model_id(model),
            )

            response = self.get_llm_orchestrator(request).execute(llm_request)
            return JsonResponse(response.results, status=200)

        except Exception as e:
            return _handle_orchestrator_error(request, e)
