from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PxNodeViewSet

router = DefaultRouter()
router.register(r"pxnodes", PxNodeViewSet, basename="pxnode")

urlpatterns = [
    path("", include(router.urls)),
]
