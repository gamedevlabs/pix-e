from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PxChartContainer, PxChartContainerLayout


@receiver(post_save, sender=PxChartContainer)
def create_node_layout(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "layout"):
        PxChartContainerLayout.objects.create(container=instance)
