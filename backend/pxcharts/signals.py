from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PxChartNode, PxChartNodeLayout


@receiver(post_save, sender=PxChartNode)
def create_node_layout(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "layout"):
        PxChartNodeLayout.objects.create(node=instance)
