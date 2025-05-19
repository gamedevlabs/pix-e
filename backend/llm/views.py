# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView

from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .gemini.GeminiLink import GeminiLink
from .models import GameDesignDescription, Pillar
from .serializers import GameDesignSerializer, PillarSerializer

# Create your views here.


class PillarViewSet(ModelViewSet):
    serializer_class = PillarSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pillar_id"

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

    def get(self, request):
        try:
            design = GameDesignDescription.objects.first()
            pillars = [pillar for pillar in Pillar.objects.all()]

            prompt = (
                f"Rate the following game design description with regards to the "
                f"following design pillars:\n"
                f"{design}\n\nPillars:\n"
            )
            prompt += f"Game Design Description: {design.description}\n"
            prompt += "Design Pillars:\n"
            for pillar in pillars:
                prompt += f"Title: {pillar.title}\n"
                prompt += f"Description: {pillar.description}\n\n"

            prompt += (
                "\nDo not use any markdown in your answer. Answer directly as "
                "if you are giving your feedback to "
                "the designer."
            )
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
            prompt = """Check if the following Game Design Pillar is written in a
                        sensible way. First validate, but only list these issues if
                        they are present otherwise ignore this section:
                        1. The title is not clear or does not match the description.
                        2. The description is not written as continuous text.
                        3. The intent of the pillar is not clear.\n
                        Then give feedback on the pillar and if it could be improved.\n
                      \n\n"""
            prompt += f"Title: {pillar.title}\n"
            prompt += f"Description: {pillar.description}\n\n"

            prompt += (
                "Do not use any markdown in your answer. Answer directly as if"
                " your giving your feedback to the "
                "designer."
            )
            answer = self.gemini.generate_response(prompt)
            return JsonResponse({"feedback": answer}, status=200)
        except Exception as e:
            return HttpResponse({"error": e}, status=404)
