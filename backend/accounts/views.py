"""Views for the accounts app — authentication and personal API-key management.

Provides user registration, login/logout, and the personal API-keys feature
(CRUD) with encryption at rest and session-scoped decryption keys.
"""

import logging

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer

from .encryption import (
    clear_key_from_session,
    derive_encryption_key,
    generate_encryption_salt,
    store_key_in_session,
)
from .models import UserApiKey, UserSalt
from .serializers import UserApiKeySerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"id": user.id}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, request):
        password = request.data.get("password", "")
        user = authenticate(
            username=request.data.get("username", ""), password=password
        )
        if user:
            login(request, user)
            salt_obj, _ = UserSalt.objects.get_or_create(
                user=user,
                defaults={"salt": generate_encryption_salt()},
            )
            key = derive_encryption_key(password, salt=bytes(salt_obj.salt))
            store_key_in_session(request.session, key)
            return Response({"id": user.id})
        return Response({"error": "Invalid credentials"}, status=400)


class LogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            clear_key_from_session(request.session)
            logout(request)
            return Response({"message": "Logged out successfully"})
        return Response({"error": "User not authenticated"}, status=401)


class MeView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return JsonResponse(
                {"id": request.user.id, "username": request.user.username}
            )
        else:
            return JsonResponse({"error": "User not authenticated"}, status=401)


class ApiKeyViewSet(viewsets.ModelViewSet):
    serializer_class = UserApiKeySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserApiKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
