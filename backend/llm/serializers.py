from rest_framework import serializers

from .models import GameDesignDescription, Pillar


class PillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pillar
        fields = ["pillar_id", "title", "description"]
        read_only_fields = ["pillar_id"]


class GameDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameDesignDescription
        fields = ["description"]
