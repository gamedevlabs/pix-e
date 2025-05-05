
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PillarViewSet, DesignView, GeneratorView

app_name = "llm"

router = DefaultRouter()
router.register(r'pillars', PillarViewSet, basename='pillars')

urlpatterns = router.urls

urlpatterns += [
    path('design/', DesignView.as_view()),
    path('feedback/', GeneratorView.as_view()),
]