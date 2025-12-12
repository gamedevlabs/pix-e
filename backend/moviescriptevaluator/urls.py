from django.urls import include, path
from rest_framework_nested import routers

from moviescriptevaluator.views import MovieProjectView, MovieScriptAssets

app_name = "moviescriptevaluator"

router = routers.SimpleRouter()
router.register(r"", MovieProjectView, basename="projects")

project_routers = routers.NestedSimpleRouter(router, r"", lookup="project")
project_routers.register(r"assets", MovieScriptAssets, basename="project-assets")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(project_routers.urls)),
]
