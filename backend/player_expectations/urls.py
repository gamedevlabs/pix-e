from django.urls import path
from . import views

urlpatterns = [
    path('api/player-expectations/', views.player_expectations_data, name='player_expectations_data'),
]

