from rest_framework import serializers

from moviescriptevaluator.models import AssetMetaData, MovieProject, MovieScript


class UnrealEngineDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetMetaData
        fields = "__all__"


class MovieProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieProject
        fields = "__all__"

class MovieScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieScript
        fields = "__all__"
