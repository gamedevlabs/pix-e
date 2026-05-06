from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ApiKeyViewSet,
    LoginView,
    LogoutView,
    MeView,
    ReestablishKeyView,
    RegisterView,
)

app_name = "accounts"

router = DefaultRouter()
router.register(r"api-keys", ApiKeyViewSet, basename="api-key")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path(
        "reestablish-key/", ReestablishKeyView.as_view(), name="reestablish-key"
    ),
    path("", include(router.urls)),
]
