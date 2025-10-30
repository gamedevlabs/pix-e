"""URL patterns for SPARC API endpoints."""

from django.urls import path

from sparc.views import SPARCMonolithicView, SPARCQuickScanView

app_name = "sparc"

urlpatterns = [
    path("quick-scan/", SPARCQuickScanView.as_view(), name="quick-scan"),
    path("monolithic/", SPARCMonolithicView.as_view(), name="monolithic"),
]
