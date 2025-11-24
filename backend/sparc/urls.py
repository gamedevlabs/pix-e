"""URL patterns for SPARC API endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from sparc.llm.views.v2 import SPARCV2AspectView, SPARCV2EvaluateView
from sparc.llm.views.v2_stream import SPARCV2StreamView
from sparc.views import (
    SPARCEvaluationViewSet,
    SPARCMonolithicView,
    SPARCQuickScanView,
)

app_name = "sparc"

router = DefaultRouter()
router.register(r"evaluations", SPARCEvaluationViewSet, basename="evaluation")

urlpatterns = [
    # V1 endpoints (no router)
    path("quick-scan/", SPARCQuickScanView.as_view(), name="quick-scan"),
    path("monolithic/", SPARCMonolithicView.as_view(), name="monolithic"),
    # V2 endpoints (router-based)
    path("v2/evaluate/", SPARCV2EvaluateView.as_view(), name="v2-evaluate"),
    path("v2/evaluate-stream/", SPARCV2StreamView.as_view(), name="v2-evaluate-stream"),
    path("v2/evaluate/aspect/", SPARCV2AspectView.as_view(), name="v2-aspect"),
    path("v2/evaluate/aspects/", SPARCV2AspectView.as_view(), name="v2-aspects"),
] + router.urls
