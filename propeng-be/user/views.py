from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .serializers import MyTokenObtainPairSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework import status, generics
from .models import User

from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully!", "user_id": user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            # Read and print the raw request body
            data = json.loads(request.body.decode('utf-8'))
            print("🔹 Incoming API Request Data:", data)  # This prints in the terminal
            logger.info(f"Received Login Request: {data}")  # Logs the request
        except Exception as e:
            print("❌ Error reading request body:", e)

        return super().post(request, *args, **kwargs)


# Login (JWT)
class LoginView(TokenObtainPairView):
    pass

# Refresh Token
class RefreshTokenView(TokenRefreshView):
    pass

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    print(request.auth)
    try:
        # Manually authenticate the token
        print(request)
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(request.auth)
        user = jwt_auth.get_user(validated_token)
        print("🔹 Validated User:", user.username)  # Log the user
    except (InvalidToken, TokenError) as e:
        print("❌ Token Error:", e)  # Log token validation errors

    return Response({"username": request.user.username})


class logout_view(APIView):
    permission_classes = [IsAuthenticated]

    def options(self, request, *args, **kwargs):
        """Allow the OPTIONS request for CORS preflight."""
        return Response(status=200)  # Respond OK to OPTIONS request

    def post(self, request):
        """Handle logout."""
        return Response({"message": "Logged out successfully"}, status=200)