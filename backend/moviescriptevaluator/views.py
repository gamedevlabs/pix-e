from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from moviescriptevaluator.serializers import UnrealEngineDataSerializer


class MovieScriptAssets(APIView):
    def post(self, request):
        serializer = UnrealEngineDataSerializer(data=request.data, many=True)
        if serializer.is_valid():
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
