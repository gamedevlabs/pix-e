from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from moviescriptevaluator.models import AssetMetaData
from moviescriptevaluator.serializers import UnrealEngineDataSerializer


class MovieScriptAssets(viewsets.ModelViewSet):
    serializer_class = UnrealEngineDataSerializer

    def get_queryset(self):
        data = AssetMetaData.objects.order_by("created_at")
        return data

    def post(self):
        serializer = UnrealEngineDataSerializer(data=self.request.data, many=True)
        if serializer.is_valid():
            print(serializer.data)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
