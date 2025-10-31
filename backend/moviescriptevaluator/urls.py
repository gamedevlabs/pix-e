from django.urls import include, path
from rest_framework_nested import routers

from moviescriptevaluator.views import MovieScriptAssets

app_name = "moviescriptevaluator"

router = routers.SimpleRouter()
router.register(r"", MovieScriptAssets, basename="movie-script-evaluator")

urlpatterns = [
    path("", include(router.urls)),
]
