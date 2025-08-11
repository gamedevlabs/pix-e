"""
Production URL Co    # Health check and status
    path("api/health/", views_production.health_check, name="health-check"),
    path("api/status/", views_production.system_status, name="system-status"),or Moodboards
Implements unified moodboard-first API endpoints
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views_production

# Create router for ViewSet-based endpoints
router = DefaultRouter()
router.register(r"moodboards", views_production.MoodboardViewSet, basename="moodboard")
router.register(
    r"images", views_production.MoodboardImageViewSet, basename="moodboard-image"
)

# Production URL patterns
urlpatterns = [
    # Production API endpoints (preferred)
    path("api/v2/", include(router.urls)),
    # Legacy compatibility endpoints
    path(
        "api/v1/generate-images/",
        views_production.generate_images_legacy,
        name="generate-images-legacy",
    ),
    path(
        "api/v1/moodboards/<int:moodboard_id>/generate/",
        views_production.generate_images_legacy,
        name="generate-images-legacy-detail",
    ),
    # Health check and status
    path("api/health/", views_production.health_check, name="health-check"),
    path("api/status/", views_production.system_status, name="system-status"),
]

# Additional patterns for convenience
app_name = "moodboards_production"
