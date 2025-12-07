from django.urls import include, path
from rest_framework_nested import routers

from moviescriptevaluator.views import MovieScriptAssets, MovieProjectView

app_name = "moviescriptevaluator"

router = routers.SimpleRouter()
router.register(r"", MovieProjectView, basename="movie-script-evaluator")
router.register(r"/assets", MovieScriptAssets, basename="asset-metadata")

urlpatterns = [
    path("", include(router.urls)),
]
