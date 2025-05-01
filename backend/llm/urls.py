
from django.urls import path

from .views import PillarView, DesignView, GeneratorView

app_name = "llm"

urlpatterns = [
    path('pillars/', PillarView.as_view()),
    path('design/', DesignView.as_view()),
    path('feedback/', GeneratorView.as_view()),
]