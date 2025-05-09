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

class OverallFeedbackView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()

    def get(self, request):
        try:
            design = GameDesignDescription.objects.first()
            pillars = [pillar for pillar in Pillar.objects.all()]

            prompt = f"Rate the following game design description with regards to the following design pillars:\n{design}\n\nPillars:\n"
            prompt += f"Game Design Description: {design.description}\n"
            prompt += f"Design Pillars:\n"
            for pillar in pillars:
                prompt += f"Title: {pillar.title}\n"
                prompt += f"Description: {pillar.description}\n\n"

            prompt += "\nDo not use any markdown in your answer. Answer directly as if your giving your feedback to the designer."
            answer = self.gemini.generate_response(prompt)
            return JsonResponse({"feedback": answer}, status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)


class PillarFeedbackView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()

    def get(self, request, pillar_id):
        try:
            pillar = Pillar.objects.filter(pillar_id=pillar_id).first()
            prompt = """Check if the following Game Design Pillar is written in a sensible way.
                        First validate, but only list these issues if they are present otherwise ignore this section:
                        1. The title is not clear or does not match the description.
                        2. The description is not written as continuous text.
                        3. The intent of the pillar is not clear.\n
                        Then give feedback on the pillar and if it could be improved.\n
                      \n\n"""
            prompt += f"Title: {pillar.title}\n"
            prompt += f"Description: {pillar.description}\n\n"

            prompt += f"Do not use any markdown in your answer. Answer directly as if your giving your feedback to the designer."
            answer = self.gemini.generate_response(prompt)
            return JsonResponse({"feedback": answer}, status=200)
        except Exception as e:
            return HttpResponse({"error": e}, status=404)
