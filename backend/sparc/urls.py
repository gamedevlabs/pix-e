"""URL patterns for SPARC API endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from sparc.views import (
    SPARCEvaluationViewSet,
    SPARCMonolithicView,
    SPARCQuickScanView,
)

app_name = "sparc"

router = DefaultRouter()
router.register(r"evaluations", SPARCEvaluationViewSet, basename="evaluation")

urlpatterns = [
    path("quick-scan/", SPARCQuickScanView.as_view(), name="quick-scan"),
    path("monolithic/", SPARCMonolithicView.as_view(), name="monolithic"),
] + router.urls
