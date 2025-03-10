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
from .models import Student, Teacher, User
from kelas.models import Kelas
import re
from django.contrib.auth.hashers import make_password
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
                    "waliKelas": Kelas.objects.filter(waliKelas_id=t.id).values_list("namaKelas", flat=True).first() or "",
                    "createdAt": t.createdAt,
                    "updatedAt": t.updatedAt
                } for t in teacher

            ] 
        }) 

'''
[PBI 10] Melihat Daftar Akun Pengguna 
'''

@api_view(['GET'])
def profile(request, id):
    try:
        akun = User.objects.get(id=id)
        
        role_akun = akun.role
        is_homeroom = False
        if role_akun == "student":
            student = Student.objects.get(username=akun.username)
            kelas = Kelas.objects.filter(siswa=student)
            namaKelas = kelas.first().namaKelas if kelas.exists() else "Belum Terdaftar"
            return JsonResponse(
                {
                    "status": 200,
                    "message": "Berhasil mendapatkan info profil",
                    "id": akun.id,
                    "student_id": student.id,
                    "role": akun.role,
                    "nama": student.name if student.name else "-",
                    "username": student.username if student.username else "-",
                    "kelas": namaKelas if kelas.exists() else "-",
                    "nisn": student.nisn if student.nisn else "-",

                }
            )
        if role_akun == "teacher":
            teacher = Teacher.objects.get(username=akun.username)
            if teacher.homeroomId != None:
                is_homeroom = True
                kelas = Kelas.objects.filter(waliKelas=teacher)
                namaKelas = kelas.first().namaKelas if kelas.exists() else "Belum Terdaftar"
            return JsonResponse(
                { 
                    "status": 200,
                    "message": "Berhasil mendapatkan informasi profil",
                    "id": akun.id,
                    "teacher_id": student.id,
                    "type": "Wali Kelas" if is_homeroom == True else "Guru",
                    "nama": teacher.name if teacher.name else "-",
                    "username": teacher.username if teacher.username else "-",
                    "kelas": namaKelas if namaKelas else "-",
                    "nisn": teacher.nisp if teacher.nisp else "-"
                    
                }
            )
        else :
            return JsonResponse(
                {
                    "status": 400,
                    "message": f"Gagal mendapatkan informasi akun {akun.username}. Role = {akun.role if akun.role else 'Belum Diassign. Cek Django Admin'}"
                }
            )
    except User.DoesNotExist as e:
        return JsonResponse(
                {
                    "status": 400,
                    "message": f"Gagal mendapatkan informasi akun. Akun tidak ditemukan",
                }
            )
    except Exception as e:
        return JsonResponse(
                {
                    "status": 400,
                    "message": f"Gagal mendapatkan informasi akun, {akun.username if akun.username else 'belum ada akunnya'}. Role = {akun.role if akun.role else 'Belum Diassign. Cek Django Admin'}. Status {e}",
                }
            )
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
                    "waliKelas": Kelas.objects.filter(waliKelas_id=t.id).values_list("namaKelas", flat=True).first() or "",
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
    active_student = Student.objects.select_related("tahunAjaran").all().filter(isDeleted=False)
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
                    "tahunAjaran": s.tahunAjaran.tahunAjaran,
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
            print(user.role)
            print("yang diaatas")
            if user.role == "student":
                print("printed student")
                return Response(
                    {"status":201,"message": "User created successfully!", "user_name": Student.objects.filter(user=user).first().name},
                    status=status.HTTP_201_CREATED
                )
            else:
                print("printed teacher")
                return Response(
                    {"status":201,"message": "User created successfully!", "user_name": Teacher.objects.filter(user=user).first().name},
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
            "id": "no can do, u cant see your id"  # Will hold student/teacher ID
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

        return Response ({"status":200,
                        "message":"Berhasil mendapatkan data user",
                        "data_user":user_data})

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
    


@api_view(['PUT'])
@permission_classes([IsAuthenticated]) 
def change_password(request):
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    # Cek apakah password lama cocok dengan yang di-hash di database
    if not user.check_password(old_password):
        return Response({"error": "Password lama salah."}, status=status.HTTP_400_BAD_REQUEST)

    # Validasi password baru (minimal 8 karakter, ada huruf besar, kecil, angka)
    if len(new_password) < 8:
        return Response({"error": "Password harus minimal 8 karakter."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.search(r'[A-Z]', new_password):
        return Response({"error": "Password harus mengandung setidaknya satu huruf besar."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.search(r'[a-z]', new_password):
        return Response({"error": "Password harus mengandung setidaknya satu huruf kecil."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.search(r'\d', new_password):
        return Response({"error": "Password harus mengandung setidaknya satu angka."}, status=status.HTTP_400_BAD_REQUEST)

    # Hash password baru sebelum menyimpan ke database
    user.password = make_password(new_password)
    user.save()

    return Response({"message": "Password berhasil diperbarui"}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # Admin harus login
def reset_password(request):
    if request.user.role != "admin":  # Pastikan hanya admin yang bisa mereset password
        return Response({"error": "Hanya admin yang bisa mereset password."}, status=status.HTTP_403_FORBIDDEN)

    user_id = request.data.get("user_id")  # ID student/teacher yang mau direset
    # new_password = request.data.get("new_password")
    new_password = "SMAKAnglo123"

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

    # Validasi password baru (minimal 8 karakter, ada huruf besar, kecil, angka)
    if len(new_password) < 8:
        return Response({"error": "Password harus minimal 8 karakter."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.search(r'[A-Z]', new_password):
        return Response({"error": "Password harus mengandung setidaknya satu huruf besar."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.search(r'[a-z]', new_password):
        return Response({"error": "Password harus mengandung setidaknya satu huruf kecil."}, status=status.HTTP_400_BAD_REQUEST)
    if not re.search(r'\d', new_password):
        return Response({"error": "Password harus mengandung setidaknya satu angka."}, status=status.HTTP_400_BAD_REQUEST)

    # Hash password baru sebelum menyimpan ke database
    user.password = make_password(new_password)
    user.save()

    return Response({"message": f"Password untuk {user.username} berhasil diperbarui"}, status=status.HTTP_200_OK)