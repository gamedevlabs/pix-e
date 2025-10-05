from django.urls import path

from .views import player_expectations_data

urlpatterns = [
    path(
        "api/player-expectations/",
        player_expectations_data,
        name="player_expectations_data",
    ),
]
