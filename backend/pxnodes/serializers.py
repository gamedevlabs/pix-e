from rest_framework import serializers

from .models import PxNode


class PxNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxNode
        fields = "__all__"
        read_only_fields = ["owner", "created_at", "updated_at"]
