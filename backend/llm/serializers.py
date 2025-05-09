from rest_framework import serializers
from .models import Pillar, GameDesignDescription


class PillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pillar
        fields = "__all__"
        read_only_fields = ["pillar_id"]

class GameDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameDesignDescription
        fields = ["game_id", "description"]