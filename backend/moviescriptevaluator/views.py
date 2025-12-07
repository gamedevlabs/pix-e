
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from moviescriptevaluator.forms import MovieScriptForm
from moviescriptevaluator.models import AssetMetaData, MovieProject
from moviescriptevaluator.serializers import UnrealEngineDataSerializer, MovieProjectSerializer


class MovieProjectView(viewsets.ModelViewSet):
    serializer_class = MovieProjectSerializer

    def get_queryset(self):
        data = MovieProject.objects.filter(owner=self.request.user).order_by("created_at")
        return data

    def create(self, request, *args, **kwargs):
        request.data["owner"] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MovieScriptAssets(viewsets.ModelViewSet):
    serializer_class = UnrealEngineDataSerializer

    def get_queryset(self):
        ## change here later and provide page for each project
        data = AssetMetaData.objects.filter(project=self.request.project).order_by(
            "created_at"
        )
        return data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # Called after validation, before response
        print(serializer.validated_data)
        serializer.save()

    @action(detail=True, methods=["post"], url_path="upload-script")
    def upload_script(self, request):
        form = MovieScriptForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return Response(form.data, status=status.HTTP_200_OK)

        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
