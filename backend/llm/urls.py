from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DesignView,
    OverallFeedbackView,
    PillarFeedbackView,
    PillarViewSet,
    TextSuggestionView,
    LLMServiceManagementView,
)

app_name = "llm"

router = DefaultRouter()
router.register(r"pillars", PillarViewSet, basename="pillars")

urlpatterns = router.urls

router = DefaultRouter()

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

urlpatterns += router.urls

urlpatterns += [
    path("feedback/", OverallFeedbackView.as_view()),
    path(
        "pillars/<int:pillar_id>/validate/",
        PillarFeedbackView.as_view(),
        name="pillar-validate",
    ),
    path("text-suggestions/", TextSuggestionView.as_view(), name="text-suggestions"),
    path("llm-services/", LLMServiceManagementView.as_view(), name="llm-services"),
]
