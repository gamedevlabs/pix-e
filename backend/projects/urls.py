"""
URL configuration for the game_concept app.
"""

from typing import List, Union

from django.urls import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet

router = DefaultRouter()
router.register(r"", ProjectViewSet, basename="project")

urlpatterns: List[Union[URLPattern, URLResolver]] = router.urls
