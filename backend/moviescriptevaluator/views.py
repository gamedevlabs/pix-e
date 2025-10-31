from rest_framework import status, viewsets
from rest_framework.response import Response

from moviescriptevaluator.models import AssetMetaData
from moviescriptevaluator.serializers import UnrealEngineDataSerializer


class MovieScriptAssets(viewsets.ModelViewSet):
    serializer_class = UnrealEngineDataSerializer

    def get_queryset(self):
        data = AssetMetaData.objects.filter(owner=self.request.user).order_by(
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
