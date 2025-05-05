
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PillarViewSet, DesignView, GeneratorView

app_name = "llm"

router = DefaultRouter()
router.register(r'pillars', PillarViewSet, basename='pillars')

urlpatterns = router.urls

router = DefaultRouter()
router.register(r'design', DesignView, basename='design')

urlpatterns += router.urls

urlpatterns += [
    path('feedback/', GeneratorView.as_view()),
]