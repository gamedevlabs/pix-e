from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from moviescriptevaluator.forms import MovieScriptForm
from moviescriptevaluator.llm_connector import MovieScriptLLMConnector
from moviescriptevaluator.models import AssetMetaData, MovieProject, MovieScript
from moviescriptevaluator.serializers import (
    MovieProjectSerializer,
    MovieScriptSerializer,
    UnrealEngineDataSerializer,
)
from pxcharts.permissions import IsOwner

_movie_script_llm_connector: MovieScriptLLMConnector | None = None


def get_llm_connector() -> MovieScriptLLMConnector:
    global _movie_script_llm_connector
    if _movie_script_llm_connector is None:
        _movie_script_llm_connector = MovieScriptLLMConnector()
    return _movie_script_llm_connector


class MovieProjectView(viewsets.ModelViewSet):
    serializer_class = MovieProjectSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        data = MovieProject.objects.filter(owner=self.request.user).order_by(
            "created_at"
        )
        return data

    def create(self, request, *args, **kwargs):
        request.data["owner"] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["GET"], url_path="analyze")
    def analyze_movie_script(self, request, pk):
        script = MovieScript.objects.filter(project=pk).first()
        assets = AssetMetaData.objects.filter(project=pk)

        response = get_llm_connector().analyze_movie_script(script, list(assets))
        return Response(response, status=status.HTTP_200_OK)


class MovieScriptAssets(viewsets.ModelViewSet):
    serializer_class = UnrealEngineDataSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == "list":
            project_id = self.kwargs["project_pk"]
            return AssetMetaData.objects.filter(project_id=project_id).order_by(
                "created_at"
            )

        return AssetMetaData.objects.filter(project=self.request.project).order_by(
            "created_at"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # Called after validation, before response
        print(serializer.validated_data)
        serializer.save()

    @action(
        detail=False,
        methods=["POST"],
        url_path="upload-script",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_script(self, request, project_pk=None):
        form = MovieScriptForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return Response(form.data, status=status.HTTP_200_OK)

        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class MovieScriptViewSet(viewsets.ModelViewSet):
    serializer_class = MovieScriptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MovieScript.objects.filter(project_id=self.kwargs["project_pk"])

    def create(self, request, *args, **kwargs):
        form = MovieScriptForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return Response(form.data, status=status.HTTP_200_OK)

        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, project_pk=None):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None, project_pk=None):
        script = self.get_object()
        script.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
