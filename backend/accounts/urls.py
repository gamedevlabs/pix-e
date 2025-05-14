from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import RegisterView, LoginView, LogoutView, MeView


app_name = "accounts"

urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('register/', RegisterView.as_view(), name="register"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('me/', MeView.as_view(), name="me"),
]