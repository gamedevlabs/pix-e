# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

# NEW: Import orchestrator instead of LLMSwitcher
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_orchestrator import LLMOrchestrator, LLMRequest

from .models import GameDesignDescription, Pillar
from .serializers import GameDesignSerializer, PillarSerializer

# Create your views here.

# Model name mapping (frontend sends "gemini"/"openai", we need actual model IDs)
MODEL_MAP = {
    "gemini": "gemini-2.0-flash-exp",
    "openai": "gpt-4o-mini"
}


def get_model_id(model_name: str) -> str:
    """Map frontend model names to actual model IDs."""
    return MODEL_MAP.get(model_name, model_name)


def format_pillars_text(pillars: list[Pillar]) -> str:
    """Format pillars as text for orchestrator."""
    return "\n".join([f"{i+1}. {p.name}: {p.description}" for i, p in enumerate(pillars)])


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
        return GameDesignDescription.objects.get(user=self.request.user)

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


class PillarFeedbackView(ViewSet):
    def __init__(self, **kwargs):
        super().__init__()
        self.orchestrator = LLMOrchestrator()

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
                data={
                    "name": pillar.name,
                    "description": pillar.description
                },
                model_id=get_model_id(model)
            )
            
            # Execute through orchestrator
            response = self.orchestrator.execute(llm_request)
            
            # Return just the results (maintains API compatibility)
            return JsonResponse(response.results, status=200)
            
        except Exception as e:
            print(f"Error in validate_pillar: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="fix")
    def fix_pillar(self, request, pk):
        try:
            pillar = Pillar.objects.filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)
            
            model = request.data.get("model", "gemini")
            
            # Create orchestrator request
            llm_request = LLMRequest(
                feature="pillars",
                operation="improve",
                data={
                    "name": pillar.name,
                    "description": pillar.description
                },
                model_id=get_model_id(model)
            )
            
            # Execute through orchestrator
            response = self.orchestrator.execute(llm_request)
            
            # Update pillar with improved version
            improved = response.results
            pillar.name = improved.get("name", pillar.name)
            pillar.description = improved.get("description", pillar.description)
            pillar.save()
            
            # Return serialized pillar
            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=200)
            
        except Exception as e:
            print(f"Error in fix_pillar: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)


class LLMFeedbackView(ViewSet):
    def __init__(self, **kwargs):
        super().__init__()
        self.orchestrator = LLMOrchestrator()

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
                return JsonResponse({"error": "No game design description found"}, status=404)
            
            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text = format_pillars_text(pillars)
            
            # Execute 3 operations (same as old evaluate_pillars_in_context)
            completeness_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={"pillars_text": pillars_text, "context": design.description},
                model_id=model_id
            )
            contradictions_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={"pillars_text": pillars_text, "context": design.description},
                model_id=model_id
            )
            additions_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={"pillars_text": pillars_text, "context": design.description},
                model_id=model_id
            )
            
            # Execute all 3
            completeness_response = self.orchestrator.execute(completeness_request)
            contradictions_response = self.orchestrator.execute(contradictions_request)
            additions_response = self.orchestrator.execute(additions_request)
            
            # Combine results (matches old PillarsInContextResponse format)
            combined_result = {
                "coverage": completeness_response.results,
                "contradictions": contradictions_response.results,
                "proposedAdditions": additions_response.results
            }
            
            return JsonResponse(combined_result, status=200)
            
        except Exception as e:
            print(f"Error in overall_feedback: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="completeness")
    def completeness(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()
            
            if not design:
                return JsonResponse({"error": "No game design description found"}, status=404)
            
            model = request.data.get("model", "gemini")
            
            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": design.description
                },
                model_id=get_model_id(model)
            )
            
            response = self.orchestrator.execute(llm_request)
            return JsonResponse(response.results, status=200)
            
        except Exception as e:
            print(f"Error in completeness: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="contradictions")
    def contradictions(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()
            
            if not design:
                return JsonResponse({"error": "No game design description found"}, status=404)
            
            model = request.data.get("model", "gemini")
            
            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": design.description
                },
                model_id=get_model_id(model)
            )
            
            response = self.orchestrator.execute(llm_request)
            return JsonResponse(response.results, status=200)
            
        except Exception as e:
            print(f"Error in contradictions: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="additions")
    def additions(self, request):
        try:
            pillars = list(Pillar.objects.filter(user=request.user))
            design = GameDesignDescription.objects.filter(
                user=self.request.user
            ).first()
            
            if not design:
                return JsonResponse({"error": "No game design description found"}, status=404)
            
            model = request.data.get("model", "gemini")
            
            llm_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": design.description
                },
                model_id=get_model_id(model)
            )
            
            response = self.orchestrator.execute(llm_request)
            return JsonResponse(response.results, status=200)
            
        except Exception as e:
            print(f"Error in additions: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

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
                    "context": context_text
                },
                model_id=get_model_id(model)
            )
            
            response = self.orchestrator.execute(llm_request)
            return JsonResponse(response.results, status=200)
            
        except Exception as e:
            print(f"Error in context: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

