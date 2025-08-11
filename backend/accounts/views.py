from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from accounts.serializers import UserSerializer, AIServiceTokenSerializer, AIServiceTokenCreateUpdateSerializer
from accounts.models import AIServiceToken


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
            return JsonResponse({"message": "Logged out successfully"})


@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_service_tokens(request):
    """
    Get all user's AI service tokens or create a new one.
    """
    if request.method == 'GET':
        tokens = AIServiceToken.objects.filter(user=request.user)
        serializer = AIServiceTokenSerializer(tokens, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = AIServiceTokenCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # Check if token already exists for this service
            existing_token = AIServiceToken.objects.filter(
                user=request.user, 
                service_type=serializer.validated_data['service_type']
            ).first()
            
            if existing_token:
                return Response(
                    {"error": f"Token for {serializer.validated_data['service_type']} already exists. Use PUT to update."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save(user=request.user)
            # Return the display version without the full token
            display_serializer = AIServiceTokenSerializer(serializer.instance)
            return Response(display_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_service_token_detail(request, service_type):
    """
    Get, update, or delete a specific AI service token.
    """
    try:
        token = AIServiceToken.objects.get(user=request.user, service_type=service_type)
    except AIServiceToken.DoesNotExist:
        return Response(
            {"error": "Token not found for this service"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = AIServiceTokenSerializer(token)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = AIServiceTokenCreateUpdateSerializer(token, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return the display version without the full token
            display_serializer = AIServiceTokenSerializer(serializer.instance)
            return Response(display_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        token.delete()
        return Response(
            {"message": f"Token for {service_type} deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
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
