from rest_framework import serializers
from .models import Pillar

class PillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pillar
        fields = ["pillar_id", "description"]