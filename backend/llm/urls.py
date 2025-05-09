
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PillarViewSet, DesignView, OverallFeedbackView, PillarFeedbackView

app_name = "llm"

router = DefaultRouter()
router.register(r'pillars', PillarViewSet, basename='pillars')

urlpatterns = router.urls

router = DefaultRouter()
router.register(r'design', DesignView, basename='design')

urlpatterns += router.urls

urlpatterns += [
    path('feedback/', OverallFeedbackView.as_view()),
    path('pillars/<int:pillar_id>/validate/', PillarFeedbackView.as_view(), name="pillar-validate"),
]