from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from accounts.serializers import UserSerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


# Create your views here.
class RegisterView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"id": user.id}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    
    def post(self, request):
        user = authenticate(
            username=request.data["username"], password=request.data["password"]
        )
        if user:
            login(request, user)
            return Response({"id": user.id})
        return Response({"error": "Invalid credentials"}, status=400)


class LogoutView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            return Response({"message": "Logged out successfully"})
        return Response({"error": "User not authenticated"}, status=401)


class MeView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    
    def get(self, request):
        if request.user.is_authenticated:
            return JsonResponse(
                {"id": request.user.id, "username": request.user.username}
            )
        else:
            return JsonResponse({"error": "User not authenticated"}, status=401)


class UsersListView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "User not authenticated"}, status=401)
        
        # Get all users except the current user (for sharing)
        users = User.objects.exclude(id=request.user.id).values('id', 'username')
        return JsonResponse({"users": list(users)})
