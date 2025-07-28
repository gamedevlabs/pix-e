# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from .llm_links.LLMSwitcher import LLMSwitcher
from .llm_links.responseSchemes import PillarsInContextResponse
from .models import GameDesignDescription, Pillar
from .serializers import GameDesignSerializer, PillarSerializer


# Create your views here.


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
        self.llmSwitcher = LLMSwitcher()

    @action(detail=True, methods=["POST"], url_path="validate")
    def validate_pillar(self, request, pk):
        try:
            pillar = Pillar.objects.filter(id=pk).first()
            model = request.data["model"]
            llm = self.llmSwitcher.get_llm(model)
            answer = llm.evaluate_pillar(pillar)

            return HttpResponse(
                answer.model_dump_json(), content_type="application/json", status=200
            )
        except Exception as e:
            print(e)
            return HttpResponse({"error": e}, status=500)

    @action(detail=True, methods=["POST"], url_path="fix")
    def fix_pillar(self, request, pk):
        try:
            pillar = Pillar.objects.filter(id=pk).first()
            llm = self.llmSwitcher.get_llm(request.data["model"])
            pillar = llm.improve_pillar(pillar)
            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=500)


class LLMFeedbackView(ViewSet):
    def __init__(self, **kwargs):
        super().__init__()
        self.llmSwitcher = LLMSwitcher()

    @action(detail=False, methods=["POST"], url_path="overall")
    def overall_feedback(self, request):
        try:
            design = GameDesignDescription.objects.filter(
                user=self.request.user).first()
            pillars = [pillar for pillar in Pillar.objects.filter(user=request.user)]

            answer: PillarsInContextResponse = None
            model = request.data["model"]
            llm = self.llmSwitcher.get_llm(model)
            answer = llm.evaluate_pillars_in_context(pillars, design.description)

            return HttpResponse(answer.model_dump_json(),
                                content_type="application/json", status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)

    @action(detail=False, methods=["POST"], url_path="completeness")
    def completeness(self, request):
        try:
            pillars = [pillar for pillar in Pillar.objects.filter(user=request.user)]
            design = GameDesignDescription.objects.filter(user=self.request.user).first()

            model = request.data["model"]
            llm = self.llmSwitcher.get_llm(model)
            answer = llm.evaluate_pillar_completeness(pillars, design.description)

            return HttpResponse(answer.model_dump_json(),
                                content_type="application/json", status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)

    @action(detail=False, methods=["POST"], url_path="contradictions")
    def contradictions(self, request):
        try:
            pillars = [pillar for pillar in Pillar.objects.filter(user=request.user)]
            design = GameDesignDescription.objects.filter(user=self.request.user).first()

            model = request.data["model"]
            llm = self.llmSwitcher.get_llm(model)
            answer = llm.evaluate_pillar_contradictions(pillars, design.description)

            return HttpResponse(answer.model_dump_json(),
                                content_type="application/json", status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)

    @action(detail=False, methods=["POST"], url_path="additions")
    def additions(self, request):
        try:
            pillars = [pillar for pillar in Pillar.objects.filter(user=request.user)]
            design = GameDesignDescription.objects.filter(user=self.request.user).first()

            model = request.data["model"]
            llm = self.llmSwitcher.get_llm(model)
            answer = llm.suggest_pillar_additions(pillars, design.description)

            return HttpResponse(answer.model_dump_json(),
                                content_type="application/json", status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)

    @action(detail=False, methods=["POST"], url_path="context")
    def context(self, request):
        try:
            pillars = [pillar for pillar in Pillar.objects.filter(user=request.user)]
            context = request.data.get("context", "")

            model = request.data["model"]
            llm = self.llmSwitcher.get_llm(model)
            answer = llm.evaluate_context_with_pillars(pillars, context)

            return HttpResponse(answer.model_dump_json(),
                                content_type="application/json", status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)