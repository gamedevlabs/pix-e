from django.urls import include, path
from rest_framework_nested import routers

from moviescriptevaluator.views import (
    MovieProjectView,
    MovieScriptAssets,
    MovieScriptViewSet,
)

app_name = "moviescriptevaluator"

router = routers.SimpleRouter()
router.register(r"projects", MovieProjectView, basename="projects")

project_routers = routers.NestedSimpleRouter(router, r"projects", lookup="project")
project_routers.register(r"assets", MovieScriptAssets, basename="project-assets")
project_routers.register(r"script", MovieScriptViewSet, basename="project-script")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(project_routers.urls)),
]
