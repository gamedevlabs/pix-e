from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CoherenceEvaluateView,
    ContextArtifactsPrecomputeView,
    ContextArtifactsResetView,
    ContextBuildView,
    ContextStrategiesView,
    PxComponentDefinitionViewSet,
    PxComponentViewSet,
    PxNodeViewSet,
    StrategyCompareView,
    StrategyEvaluateView,
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
    # Context Strategy API (thesis research)
    path(
        "context/strategies/",
        ContextStrategiesView.as_view(),
        name="context-strategies",
    ),
    path(
        "context/evaluate/",
        StrategyEvaluateView.as_view(),
        name="context-evaluate",
    ),
    path(
        "context/compare/",
        StrategyCompareView.as_view(),
        name="context-compare",
    ),
    path(
        "context/build/",
        ContextBuildView.as_view(),
        name="context-build",
    ),
    path(
        "context/precompute/",
        ContextArtifactsPrecomputeView.as_view(),
        name="context-precompute",
    ),
    path(
        "context/precompute/reset/",
        ContextArtifactsResetView.as_view(),
        name="context-precompute-reset",
    ),
]
