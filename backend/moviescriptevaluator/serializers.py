from rest_framework import serializers

from moviescriptevaluator.models import AssetMetaData


class UnrealEngineDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetMetaData
        fields = '__all__'

