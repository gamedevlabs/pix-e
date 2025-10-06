from django.urls import path

from moviescriptevaluator.views import MovieScriptAssets

app_name = 'moviescriptevaluator'

urlpatterns = [
    path("", MovieScriptAssets.as_view(), name="movie-script-assets"),
]