from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (PxComponentDefinitionViewSet, PxComponentViewSet,
                    PxNodeViewSet)

router = DefaultRouter()
router.register(r"pxnodes", PxNodeViewSet, basename="pxnode")
router.register(r"pxcomponents", PxComponentViewSet, basename="pxcomponent")
router.register(
    r"pxcomponentdefinitions",
    PxComponentDefinitionViewSet,
    basename="pxcomponentdefinition",
)

urlpatterns = [
    path("", include(router.urls)),
]
