# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView
from uuid import uuid4

from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Pillar, GameDesignDescription
from .gemini.GeminiLink import GeminiLink
from .serializers import PillarSerializer


# Create your views here.

class PillarViewSet(ModelViewSet):
    queryset = Pillar.objects.all()
    serializer_class = PillarSerializer

class DesignView(APIView):
    def get(self, request):
        userid = request.COOKIES.get("anon_id")
        if userid is None:
            return JsonResponse({"error": "anon_id cookie not set"}, status=400)
        try:
            design = GameDesignDescription.objects.get(user_id=userid)
            return JsonResponse({"description": design.description}, status=200)
        except GameDesignDescription.DoesNotExist:
            return JsonResponse({"description": ""}, status=200)

    def post(self, request):
        userid = request.COOKIES.get("anon_id")
        if userid is None:
            return JsonResponse({"error": "anon_id cookie not set"}, status=400)
        GameDesignDescription.objects.filter(user_id=userid).update_or_create(user_id=userid, defaults={"description": request.data["description"]})
        return HttpResponse(status=200)


class GeneratorView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()

    def get(self, request):
        try:
            design = GameDesignDescription.objects.first()
            pillars = [pillar.description for pillar in Pillar.objects.all()]

            prompt = f"Rate the following game description with regards to the following pillars:\n\n{design}\n\nPillars:\n"
            for pillar in pillars:
                prompt += f"- {pillar}\n"

            prompt += "\n Do not use any markdown symbols in your answer, simply answer in plain text"
            answer = self.gemini.generate_text(prompt)
            return JsonResponse({"feedback": answer}, status=200)
        except GameDesignDescription.DoesNotExist | GameDesignDescription.MultipleObjectsReturned:
            return HttpResponse({"error": "GameDesignDescription not found"}, status=404)
        except Pillar.DoesNotExist:
            return HttpResponse({"error": "No Pillars found"}, status=404)
