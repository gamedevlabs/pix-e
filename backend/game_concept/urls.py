"""
URL configuration for the game_concept app.
"""

from typing import List, Union

from django.urls import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from .views import GameConceptViewSet

router = DefaultRouter()
router.register(r"", GameConceptViewSet, basename="game-concept")

urlpatterns: List[Union[URLPattern, URLResolver]] = router.urls
