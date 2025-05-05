from rest_framework import serializers
from .models import Pillar, GameDesignDescription


class PillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pillar
        fields = ["pillar_id", "description"]
        read_only_fields = ["pillar_id"]

class GameDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameDesignDescription
        fields = ["game_id", "description"]