from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DesignView,
    LLMFeedbackView,
    PillarFeedbackView,
    PillarViewSet,
)

app_name = "pillars"

router = DefaultRouter()
router.register(r"pillars", PillarViewSet, basename="pillars")
router.register(r"pillars", PillarFeedbackView, basename="pillar-feedback")
router.register(r"feedback", LLMFeedbackView, basename="llm-feedback")

urlpatterns = router.urls


designView = DesignView.as_view(
    {
        "get": "retrieve",
        "put": "update",
    }
)
urlpatterns += [path("design/", designView, name="design")]
designCreate = DesignView.as_view(
    {
        "get": "get_or_create",
    }
)
urlpatterns += [
    path("design/get_or_create/", designCreate, name="design-get_or_create")
]
