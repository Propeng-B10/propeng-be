from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .serializers import MyTokenObtainPairSerializer

from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)

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
    print(request)
    try:
        # Manually authenticate the token
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(request.auth)
        user = jwt_auth.get_user(validated_token)
        print("🔹 Validated User:", user.username)  # Log the user
    except (InvalidToken, TokenError) as e:
        print("❌ Token Error:", e)  # Log token validation errors

    return Response({"username": request.user.username})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # Optionally, you can blacklist the token here
    # For now, we'll just return a success message
    return Response({"message": "Logged out successfully"})