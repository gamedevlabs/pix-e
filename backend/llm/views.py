# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .llm_links import PillarPrompts
from .llm_links.GeminiLink import GeminiLink
from .llm_links.OpenAILink import OpenAILink
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


class OverallFeedbackView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()
        self.openai = OpenAILink()

    def post(self, request):
        try:
            design = GameDesignDescription.objects.first()
            pillars = [pillar for pillar in Pillar.objects.filter(user=request.user)]

            prompt = PillarPrompts.OverallFeedbackPrompt % (
                design.description,
                "\n".join(
                    [f"{pillar.name}:\n {pillar.description}" for pillar in pillars]
                ),
            )
            model = request.data["model"]
            answer = None
            match model:
                case "gemini":
                    answer = self.gemini.generate_response(prompt)
                case "openai":
                    answer = self.openai.generate_response(prompt)

            return JsonResponse({"feedback": answer}, status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)


class PillarFeedbackView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()
        self.openai = OpenAILink()

    def post(self, request, id):
        try:
            pillar = Pillar.objects.filter(id=id).first()
            model = request.data["model"]
            answer = None
            match model:
                case "gemini":
                    answer = self.gemini.generate_pillar_response(pillar)
                case "openai":
                    answer = self.openai.generate_pillar_response(pillar)

            print(answer)
            return HttpResponse(
                answer.model_dump_json(), content_type="application/json", status=200
            )
        except Exception as e:
            print(e)
            return HttpResponse({"error": e}, status=500)


class FixPillarView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()

    def post(self, request, id):
        try:
            pillar = Pillar.objects.filter(id=id).first()
            pillar = self.gemini.fix_pillar_through_llm(pillar)
            data = PillarSerializer(pillar).data
            print("Fixed Pillar")
            return JsonResponse(data, status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=500)
