from rest_framework_nested import routers
from django.urls import path, include
from moviescriptevaluator.views import MovieScriptAssets

app_name = 'moviescriptevaluator'

router = routers.SimpleRouter()
router.register(r"", MovieScriptAssets, basename="movie-script-evaluator")

urlpatterns = [
    path("", include(router.urls)),
]