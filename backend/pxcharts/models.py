from django.contrib.auth import get_user_model
from django.db import models

from pxnodes.models import PxLockDefinition, PxNode

import uuid

User = get_user_model()


class PxChart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField()
    associatedNode = models.ForeignKey(
        PxNode, on_delete=models.SET_NULL, null=True, blank=True, related_name="charts"
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="pxcharts",
    )

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "px chart"
        verbose_name_plural = "px charts"

    def __str__(self):
        return self.name


class PxChartContainer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="containers"
    )
    content = models.ForeignKey(
        PxNode, on_delete=models.SET_NULL, null=True, blank=True
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    sourceHandle = models.CharField(max_length=255, default="")
    targetHandle = models.CharField(max_length=255, default="")

    bidirectional = models.BooleanField(default=False)

    source = models.ForeignKey(
        PxChartContainer,
        on_delete=models.SET_NULL,
        null=True,
        related_name="outgoing_edges",
    )
    target = models.ForeignKey(
        PxChartContainer,
        on_delete=models.SET_NULL,
        null=True,
        related_name="incoming_edges",
    )

    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="edges"
    )

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


class PxLockAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    count = models.IntegerField()

    definition = models.ForeignKey(PxLockDefinition, on_delete=models.CASCADE)

    edge = models.ForeignKey(PxChartEdge, on_delete=models.CASCADE)

    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="locks"
    )

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["owner", "id"]

    def __str__(self):
        return f"{self.count}x Lock {self.definition.name} on {self.edge}"


class PxChartPathSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    px_chart = models.ForeignKey(
        PxChart, on_delete=models.CASCADE, related_name="settings"
    )

    use_locks = models.BooleanField()
    ignore_consumable_keys = models.BooleanField()
    show_soft_locks = models.BooleanField()

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["owner", "id"]

    def __str__(self):
        return f"Uses Locks: {self.use_locks}, \
            Ignores Consumable Locks: {self.ignore_consumable_keys}, \
            Shows Soft Locks: {self.show_soft_locks}"
