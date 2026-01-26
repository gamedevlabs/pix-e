from rest_framework import serializers

from moviescriptevaluator.models import (
    AssetMetaData,
    MovieProject,
    MovieScript,
    ScriptSceneAnalysisResult,
    RequiredAssets
)


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


class ScriptSceneAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptSceneAnalysisResult
        fields = [
            "id",
            "project",
            "scene",
            "asset_name",
            "asset_type",
            "fab_search_keyword",
            "notes",
        ]

class RequiredAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredAssets
        fields = "__all__"
