from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from pxnodes.models import PxNode

User = get_user_model()


# Create your models here.
class PxChart(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField()

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "px chart"
        verbose_name_plural = "px charts"

    def __str__(self):
        return self.name


class PxChartContainer(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)

    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="containers"
    )
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    content_id = models.UUIDField(null=True, blank=True)
    content = GenericForeignKey('content_type', 'content_id')

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "px chart container"
        verbose_name_plural = "px chart containers"

    def __str__(self):
        return self.name


class PxChartContainerLayout(models.Model):
    container = models.OneToOneField(
        PxChartContainer, on_delete=models.CASCADE, related_name="layout"
    )
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    height = models.FloatField(default=0)
    width = models.FloatField(default=0)

    class Meta:
        verbose_name = "px chart container layout"
        verbose_name_plural = "px chart container layouts"


class PxChartEdge(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)

    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="edges"
    )
    source = models.ForeignKey(
        PxChartContainer,
        on_delete=models.SET_NULL,
        null=True,
        related_name="outgoing_edges",
    )
    sourceHandle = models.CharField(max_length=255, default="")
    target = models.ForeignKey(
        PxChartContainer,
        on_delete=models.SET_NULL,
        null=True,
        related_name="incoming_edges",
    )
    targetHandle = models.CharField(max_length=255, default="")

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "px chart edge"
        verbose_name_plural = "px chart edges"
        constraints = [
            models.UniqueConstraint(
                fields=["px_chart", "source", "sourceHandle", "target", "targetHandle"],
                name="unique_edge",
            )
        ]

    def __str__(self):
        return f"{self.px_chart.name}: {self.source.name} --- ({self.target.name})"
