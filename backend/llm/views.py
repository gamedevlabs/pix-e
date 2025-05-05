# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView
from uuid import uuid4

from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Pillar, GameDesignDescription
from .gemini.GeminiLink import GeminiLink
from .serializers import PillarSerializer, GameDesignSerializer


# Create your views here.

class PillarViewSet(ModelViewSet):
    queryset = Pillar.objects.all()
    serializer_class = PillarSerializer

class DesignView(ModelViewSet):
    queryset = GameDesignDescription.objects.all()
    serializer_class = GameDesignSerializer

    @action(detail=True, methods=['GET'], url_path='get_or_create')
    def get_or_create(self, request, pk=None):
        data = request.data
        design_id = pk

        obj, created = GameDesignDescription.objects.get_or_create(
            game_id=design_id,
            defaults={
                'description': data.get('description', ''),
            }
        )
        serializer = self.get_serializer(obj)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

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
