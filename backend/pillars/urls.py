from rest_framework.routers import DefaultRouter

from .views import (
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
