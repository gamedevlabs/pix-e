from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# Create your models here.
class PxChart(models.Model):
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


class PxChartNode(models.Model):
    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="nodes"
    )
    name = models.CharField(max_length=255)
    content = models.JSONField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "px chart node"
        verbose_name_plural = "px chart nodes"

    def __str__(self):
        return self.name


class PxChartEdge(models.Model):
    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="edges"
    )
    source = models.ForeignKey(
        PxChartNode, on_delete=models.CASCADE, related_name="outgoing_edges"
    )
    destination = models.ForeignKey(
        PxChartNode, on_delete=models.CASCADE, related_name="incoming_edges"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "px chart edge"
        verbose_name_plural = "px chart edges"
        constraints = [
            models.UniqueConstraint(
                fields=["px_chart", "source", "destination"], name="unique_edge"
            )
        ]

    def __str__(self):
        return f"{self.px_chart.name}: {self.source.name} --- ({self.destination.name})"
