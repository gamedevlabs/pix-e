from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    UsersListView,
    ai_service_tokens,
    ai_service_token_detail,
)

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("users/", UsersListView.as_view(), name="users"),
    path("ai-tokens/", ai_service_tokens, name="ai_service_tokens"),
    path(
        "ai-tokens/<str:service_type>/",
        ai_service_token_detail,
        name="ai_service_token_detail",
    ),
]
