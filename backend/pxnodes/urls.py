from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CoherenceEvaluateView,
    PxComponentDefinitionViewSet,
    PxComponentViewSet,
    PxNodeViewSet,
    StructuralMemoryGenerateView,
    StructuralMemoryStatsView,
)

router = DefaultRouter()
router.register(r"pxnodes", PxNodeViewSet, basename="pxnode")
router.register(r"pxcomponents", PxComponentViewSet, basename="pxcomponent")
router.register(
    r"pxcomponentdefinitions",
    PxComponentDefinitionViewSet,
    basename="pxcomponentdefinition",
)

urlpatterns = [
    path("", include(router.urls)),
    # Structural Memory API
    path(
        "structural-memory/generate/",
        StructuralMemoryGenerateView.as_view(),
        name="structural-memory-generate",
    ),
    path(
        "structural-memory/stats/",
        StructuralMemoryStatsView.as_view(),
        name="structural-memory-stats",
    ),
    path(
        "structural-memory/evaluate/",
        CoherenceEvaluateView.as_view(),
        name="structural-memory-evaluate",
    ),
]
