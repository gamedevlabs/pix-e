from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DesignView, OverallFeedbackView, PillarFeedbackView, PillarViewSet, \
    FixPillarView

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

# router.register(r'design', designView, basename='design')

urlpatterns += router.urls

urlpatterns += [
    path("feedback/", OverallFeedbackView.as_view()),
    path(
        "pillars/<int:id>/validate/",
        PillarFeedbackView.as_view(),
        name="pillar-validate",
    ),
    path(
        "pillars/<int:id>/fix/",
        FixPillarView.as_view(),
        name="pillar-fix",
    )
]
