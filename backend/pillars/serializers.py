from rest_framework import serializers

from .models import GameDesignDescription, Pillar


class PillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pillar
        fields = ["id", "name", "description"]


class GameDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameDesignDescription
        fields = ["description"]
