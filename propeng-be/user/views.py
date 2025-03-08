from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth.models import User
from .serializers import MyTokenObtainPairSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework import status, generics
from .models import Student, Teacher, User, TahunAjaran

from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)


'''
[PBI 2] Melihat Daftar Akun Pengguna 
'''

# Mendapatkan info dropdown list semua guru (aktif dan tidak)
@api_view(['GET'])
def list_teacher(request):
    teacher = Teacher.objects.all().order_by('-updatedAt')

    if not teacher.exists():
        return JsonResponse({
            "status":400, 
            "message":"Belum ada guru yang ditambahkan", 
            }) 
    return JsonResponse({
        "status":200, 
        "message":"Sukses menampilkan list guru", 
        "data": 
            [
                {
                    "id": t.id,
                    "name": t.name,
                    "nisp": t.nisp,
                    "username": t.username,
                    "createdAt": t.createdAt,
                    "updatedAt": t.updatedAt
                } for t in teacher

            ] 
        }) 

# Mendapatkan info dropdown list guru aktif
@api_view(['GET'])
def list_active_teacher(request):
    active_teacher = Teacher.objects.all().filter(isDeleted=False)
    teacher = active_teacher.order_by('-updatedAt')

    if not teacher.exists():
        return JsonResponse({
            "status":400, 
            "message":"Belum ada guru yang ditambahkan", 
            }) 
    return JsonResponse({
        "status":200, 
        "message":"Sukses menampilkan list guru", 
        "data": 
            [
                {
                    "id": t.id,
                    "name": t.name,
                    "nisp": t.nisp,
                    "username": t.username,
                    "createdAt": t.createdAt,
                    "updatedAt": t.updatedAt
                } for t in teacher

            ] 
        }) 

# Mendapatkan info dropdown list semua murid (aktif dan tidak)
@api_view(['GET'])
def list_student(request):
    student = Student.objects.select_related("tahunAjaran").all().order_by('-updatedAt')

    if not student.exists():
        return JsonResponse({
            "status":400, 
            "message":"Belum ada murid yang ditambahkan", 
            }) 
    return JsonResponse({
        "status":200, 
        "message":"Sukses menampilkan list murid", 
        "data": 
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "nisn": s.nisn,
                    "username": s.username,
                    "tahunAjaran": s.tahunAjaran.tahunAjaran,
                    "createdAt": s.createdAt,
                    "updatedAt": s.updatedAt
                } for s in student
            ] 
        }) 

# Mendapatkan info dropdown list murid aktif
@api_view(['GET'])
def list_active_student(request):
    active_student = Student.objects.all().filter(isDeleted=False)
    student = active_student.order_by('-updatedAt')

    if not student.exists():
        return JsonResponse({
            "status":400, 
            "message":"Belum ada murid yang ditambahkan", 
            }) 
    return JsonResponse({
        "status":200, 
        "message":"Sukses menampilkan list murid", 
        "data": 
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "nisn": s.nisn,
                    "username": s.username,
                    "tahunAjaran": s.tahunAjaran_id,
                    "createdAt": s.createdAt,
                    "updatedAt": s.updatedAt
                } for s in student
            ] 
        }) 

class IsAdminRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')
    

# request.user.is_superuser

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Require JWT authentication and that the user is authenticated
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]

    def create(self, request, *args, **kwargs):
        # Log the Authorization header (if provided)
        auth_header = request.headers.get('Authorization')
        print("Authorization header:", auth_header)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User created successfully!", "user_id": user.id},
                status=status.HTTP_201_CREATED
            )
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
    try:
        user = request.user  # Use request.user directly

        # Initialize response data
        user_data = {
            "user_id": user.id,  # Store the original user ID
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "id": None  # Will hold student/teacher ID
        }

        # Fetch role-specific ID
        if user.role == "student":
            student = Student.objects.filter(user=user).first()
            if student:
                user_data["id"] = student.id  # Use student ID
                user_data["nisn"] = student.nisn
                user_data["tahun_ajaran"] = student.tahunAjaran
            else:
                return Response({"error": "Student record not found"}, status=404)

        elif user.role == "teacher":
            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                user_data["id"] = teacher.id  # Use teacher ID
                user_data["nisp"] = teacher.nisp
                user_data["homeroom_id"] = teacher.homeroomId
            else:
                return Response({"error": "Teacher record not found"}, status=404)

        return Response(user_data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)  # Catch unexpected errors



class logout_view(APIView):
    permission_classes = [IsAuthenticated]

    def options(self, request, *args, **kwargs):
        """Allow the OPTIONS request for CORS preflight."""
        return Response(status=200)  # Respond OK to OPTIONS request

    def post(self, request):
        """Handle logout."""
        return Response({"message": "Logged out successfully"}, status=200)