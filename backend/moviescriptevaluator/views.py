from django.core.paginator import Paginator
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from moviescriptevaluator.forms import MovieScriptForm
from moviescriptevaluator.llm.schemas import RecommendationResult
from moviescriptevaluator.llm_connector import MovieScriptLLMConnector
from moviescriptevaluator.models import (
    AssetMetaData,
    MovieProject,
    MovieScript,
    ScriptSceneAnalysisResult, RequiredAssets,
)
from moviescriptevaluator.serializers import (
    MovieProjectSerializer,
    MovieScriptSerializer,
    ScriptSceneAnalysisSerializer,
    UnrealEngineDataSerializer, RequiredAssetSerializer,
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
        script_id = request.query_params.get("script_id")

        if not script_id:
            return Response(
                "Please select a script to analyze", status=status.HTTP_400_BAD_REQUEST
            )

        script = MovieScript.objects.filter(project=pk, id=script_id).first()
        if not script:
            return Response(
                "Script couldn't be found", status=status.HTTP_400_BAD_REQUEST
            )

        response = get_llm_connector().analyze_movie_script(script)
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=True, methods=["GET"], url_path="recommendations")
    def get_recommendations(self, request, pk):
        page_size = 45
        page_number = 1

        needed_items = list(ScriptSceneAnalysisResult.objects.filter(project=pk))
        items_from_ue_db = AssetMetaData.objects.filter(project=pk).order_by("created_at")
        paginator = Paginator(items_from_ue_db, page_size)

        if not needed_items:
            return Response("Please analyze the uploaded script first", status=status.HTTP_400_BAD_REQUEST)

        response: RecommendationResult = RecommendationResult(result=[])

        while True:
            page = paginator.get_page(page_number)
            items_from_ue = list(page.object_list)
            try:
                r = get_llm_connector().create_recommendations(needed_items, items_from_ue)
                response.result += r.result
            except:
                print("error")

            if page.has_next():
                page_number = page.next_page_number()
            else:
                break

        # Remove the duplicates
        unique_assets = []
        seen_names = set()

        for item in response.result:
            if item.asset_name not in seen_names:
                unique_assets.append(item)
                seen_names.add(item.asset_name)

        response.result = unique_assets

        # Delete all the previous recommendations
        RequiredAssets.objects.filter(project=pk).delete()

        for item in response.result:
            try:
                asset_in_db = AssetMetaData.objects.filter(project=pk, name=item.asset_name).first()
                project = MovieProject.objects.get(pk=pk)

                RequiredAssets.objects.create(
                    asset=asset_in_db,
                    project=project,
                    name=item.asset_name,
                    purpose=item.purpose,
                    description=item.description,
                )
            except AssetMetaData.DoesNotExist:
                continue

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


class ScriptSceneAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = ScriptSceneAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScriptSceneAnalysisResult.objects.filter(
            project=self.kwargs["project_pk"]
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        existing_items = ScriptSceneAnalysisResult.objects.filter(
            project=self.kwargs["project_pk"]
        )
        existing_items.delete()

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None, project_pk=None):
        script = self.get_object()
        script.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RequiredAssetViewSet(viewsets.ModelViewSet):
    serializer_class = RequiredAssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RequiredAssets.objects.filter(
            project=self.kwargs["project_pk"]
        )