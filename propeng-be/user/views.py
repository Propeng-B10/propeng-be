from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth.models import User
from .serializers import MyTokenObtainPairSerializer, UserSerializer, ChangePasswordSerializer
from rest_framework.views import APIView
from rest_framework import status, generics, serializers
from .models import Student, Teacher, User
from kelas.models import Kelas
from tahunajaran.models import Angkatan
from absensi.models import *
import re
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import json
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class IsAdminRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsTeacherRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'teacher')
    
class IsStudentRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')


class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(instance=request.user, data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()  # Calls update() method
            return Response({"status": "200", "message": "Password changed successfully"}, status=status.HTTP_200_OK)

        return Response({"status": "400", "message": "Password failed to change", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



'''
[PBI 2] Melihat Daftar Akun Pengguna 
'''



# Mendapatkan info dropdown list semua guru (aktif dan tidak)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teacher(request):
    """List all teachers, including both active and deleted"""
    try:
        teachers = Teacher.objects.filter(isDeleted=False)
        teacher_list = []
        
        for teacher in teachers:
            teacher_data = {
                "id": teacher.user_id,
                "name": teacher.name,
                "username": teacher.user.username,  # Using synchronized username
                "nisp": teacher.nisp,
                "angkatan": teacher.angkatan.angkatan if teacher.angkatan else None, 
                "isActive": teacher.user.is_active
            }
            teacher_list.append(teacher_data)
            
        return Response({
            "status": 200,
            "message": "Successfully retrieved teacher list",
            "data": teacher_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving teacher list: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

'''
[PBI 2] Melihat Daftar Akun Pengguna 
'''

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request, id):
    """Get detailed profile information for a user"""
    try:
        user = User.objects.get(id=id)
        print("yes profile")
        # Initialize base profile data
        profile_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            'createdAt':user.createdAt,
            'updatedAt':user.updatedAt
        }
        print("here profile")
        print(profile_data)
        # Add role-specific data
        if user.role == "student":
            student = Student.objects.filter(user=user).first()
            try:
                active_classes = student.siswa.get(isActive=True, isDeleted=False)
            except :
                active_classes = None
            # .values_list('namaKelas', flat=True)
            statusAbsen = None
            print("workss")
            if active_classes:
                print("kejalan")
                print(active_classes)
                today = timezone.now().date()
                absensi = AbsensiHarian.objects.filter(kelas_id=active_classes.id, date=today).first()
                if absensi:
                    statusAbsen = absensi.check_absensi(int(user.id))
            print("doenst")
            print("works")
            print("diatas if student")
            if student:
                print(student.name)
                print(student.nisn)
                print(active_classes.namaKelas if active_classes else None)
                print(active_classes.id if active_classes else None)
                print(statusAbsen if statusAbsen else None)
                print("disini loh")
                
                profile_data.update({
                    "name": student.name,
                    "nisn": student.nisn,
                    "angkatan": student.angkatan.angkatan if student.angkatan else None,
                    "isActive": student.isActive,
                    "isAssignedtoClass":student.isAssignedtoClass,
                    "activeClasses": active_classes.namaKelas if active_classes else None,
                    "classId":active_classes.id if active_classes else None,
                    "sudahAbsen":statusAbsen if statusAbsen else None
                })
                print(profile_data)
                
        elif user.role == "teacher":
            print("works")
            teacher = Teacher.objects.filter(user=user).first()
            print("disini profile")
            homeroom_class = teacher.homeroomId.namaKelas if teacher.homeroomId and not teacher.homeroomId.isDeleted and teacher.homeroomId.isActive else None
            print(teacher.homeroomId)
            print("homeroom diatas")
            if teacher:
                profile_data.update({
                    "name": teacher.name,
                    "nisp": teacher.nisp,
                    "angkatan":teacher.angkatan.angkatan if teacher.angkatan else None,
                    "isActive": user.is_active,
                    "namaHomeroomClass" :homeroom_class if homeroom_class else None,
                    "homeroomId" : teacher.homeroomId_id if homeroom_class else None,
                    # still none, nanti kita tambahin kalo mau hehe
                })
            print("here dibawah gw homeroom_class")
            if homeroom_class:
                print("shouldnt be here")
                teacher_classes = Kelas.objects.filter(
                    waliKelas=teacher,
                    isActive=True,
                    isDeleted=False
                ).order_by('-updatedAt')
                for k in teacher_classes:
                    # Get the total count of students
                    total_students = k.siswa.count()
                    
                    # Initialize attendance counters
                    total_alfa = 0
                    total_hadir = 0
                    total_sakit = 0
                    total_izin = 0
                    print("theree")
                    # Get the most recent absensi record for this class if it exists
                    latest_absensi = AbsensiHarian.objects.filter(kelas=k).order_by('-date').first()
                    print("thisss")
                    if latest_absensi:
                        total_alfa = 0
                        total_hadir = 0
                        total_sakit = 0
                        total_izin = 0
                        # Count attendance statuses
                        for student_id, data in latest_absensi.listSiswa.items():
                            if isinstance(data, dict):
                                status1 = data.get("status", "")
                            else:
                                status1 = data

                            print(status1)
                            if status1 == "Alfa":
                                total_alfa += 1
                            elif status1 == "Hadir":
                                total_hadir += 1
                            elif status1 == "Sakit":
                                total_sakit += 1
                            elif status1 == "Izin":
                                total_izin += 1
                        print("it gets here")
                        profile_data.update({
                            "totalSiswa": total_students,
                            "absensiStats": {
                                "totalAlfa": total_alfa,
                                "totalHadir": total_hadir,
                                "totalSakit": total_sakit,
                                "totalIzin": total_izin
                            },
                        })          
                        print(profile_data)    
        return Response({
            "status": 200,
            "message": "Successfully retrieved user profile",
            "data": profile_data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            "status": 404,
            "message": f"User with ID {id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving user profile: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Mendapatkan info dropdown list guru aktif
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_active_teacher(request):
    """List only active teachers (not deleted)"""
    try:
        teachers = Teacher.objects.filter(isDeleted=False)
        teacher_list = []
        
        for teacher in teachers:
            teacher_data = {
                "id": teacher.user_id,
                "name": teacher.name,
                "username": teacher.user.username,  # Using synchronized username
                "nisp": teacher.nisp,
                "angkatan":teacher.angkatan.angkatan if teacher.angkatan else None,
                "homeroomId": teacher.homeroomId.id if teacher.homeroomId else None, 
                "isActive": teacher.user.is_active
            }
            teacher_list.append(teacher_data)
            
        return Response({
            "status": 200,
            "message": "Successfully retrieved active teacher list",
            "data": teacher_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving active teacher list: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_homeroom_teachers(request):
    """List teachers who are assigned as homeroom teachers (have homeroomId)"""
    try:
        # Filter teachers who have a non-null homeroomId
        teachers = Teacher.objects.filter(homeroomId__isnull=False, isDeleted=False)
        teacher_list = []
        
        for teacher in teachers:
            teacher_data = {
                "id": teacher.user_id,
                "name": teacher.name,
                "username": teacher.user.username,
                "nisp": teacher.nisp,
                "angkatan":teacher.angkatan.angkatan if teacher.angkatan else None,
                "homeroomId": teacher.homeroomId.namaKelas,
                "isActive": teacher.user.is_active
            }
            teacher_list.append(teacher_data)
            
        return Response({
            "status": 200,
            "message": "Successfully retrieved list of homeroom teachers",
            "data": teacher_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving homeroom teacher list: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Mendapatkan info dropdown list semua murid (aktif dan tidak)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_student(request):
    """List all students, including both active and deleted"""
    try:
        students = Student.objects.filter(isDeleted=False)
        student_list = []
        
        for student in students:
            student_data = {
                "id": student.user_id,
                "name": student.name,
                "isAssignedtoClass": student.isAssignedtoClass,
                "username": student.user.username,  # Using synchronized username
                "nisn": student.nisn,
                "angkatan": student.angkatan.angkatan if student.angkatan else None,
                "status": "Deleted" if student.isDeleted else "Active"
            }
            student_list.append(student_data)
            
        return Response({
            "status": 200,
            "message": "Successfully retrieved student list",
            "data": student_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving student list: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Mendapatkan info dropdown list murid aktif
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_active_student(request):
    """List only active students (not deleted)"""
    try:
        print("yes")
        students = Student.objects.filter(isDeleted=False)
        print(students)
        student_list = []
        
        if students.kelas.isActive == False:
            students = students.kelas.filter(isActive=False, isDeleted=False)
        for student in students:
            # Ambil semua kelas yang tertaut ke siswa
            kelas_terkait = student.siswa.all()  # `siswa` adalah related_name dari Kelas ke Student

            # Cek apakah ada kelas tidak aktif
            if kelas_terkait.filter(isActive=False).exists():
                student.isActive = False
                student.save(update_fields=['isActive'])
            else:
                # Pastikan siswa aktif jika tidak ada kelas tidak aktif
                student.isActive = True
                student.save(update_fields=['isActive'])
            student_data = {
                "id": student.user_id,
                "name": student.name,
                "isAssignedtoClass": student.isAssignedtoClass,
                "username": student.user.username,  # Using synchronized username
                "nisn": student.nisn,
                "angkatan": student.angkatan.angkatan if student.angkatan else None,
                "status": "Active"
            }
            student_list.append(student_data)
            
        return Response({
            "status": 200,
            "message": "Successfully retrieved active student list",
            "data": student_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving active student list: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    serializer_class = MyTokenObtainPairSerializer
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
            "role": user.role
        }

        if user.role == "student":
            student = Student.objects.filter(user=user).first()
            if student:
                user_data["name"] = student.name
                user_data["id"] = student.user_id 
                user_data["nisn"] = student.nisn
                user_data["angkatan"] = student.angkatan.angkatan
                user_data["isAssignedtoClass"] = student.isAssignedtoClass
            else:
                return Response({"error": "Student record not found"}, status=404)

        elif user.role == "teacher":
            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                user_data["name"] = teacher.name
                user_data["id"] = teacher.user_id 
                user_data["nisp"] = teacher.nisp
                user_data["angkatan"] = teacher.angkatan.angkatan
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
        return Response(status=200) 

    def post(self, request):
        """Handle logout."""
        return Response({"message": "Logged out successfully"}, status=200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    if request.user.role != "admin":
        return Response({"error": "Hanya admin yang bisa mereset password."}, status=status.HTTP_403_FORBIDDEN)

    user_id = request.data.get("user_id")
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

# Update and delete user

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminRole])
def delete_user(request, id):
    """Soft delete a user by setting isDeleted to True"""
    try:
        user = User.objects.get(id=id)
        
        if user.role == "student":
            student = Student.objects.filter(user=user).first()
            if student:
                # kalo true otomatis brrt ada di kelas harusnya T^T
                if student.siswa.exists():
                    return Response({
                        "status": 400,
                        "message": f"Tidak bisa menghapus siswa {student.name} karena siswa tersebut telah masuk ke suatu Kelas. Silahkan keluarkan siswa tersebut dahulu sebelum menghapus siswa."
                    }, status=status.HTTP_400_BAD_REQUEST)
            
                if student.matapelajaran.exists():
                    return Response({
                        "status": 400,
                        "message": f"Tidak bisa menghapus siswa {student.name} karena siswa tersebut telah masuk ke suatu Mata Pelajaran. Silahkan keluarkan siswa tersebut dahulu sebelum menghapus siswa."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                student.isDeleted = True
                student.save()
                return Response({
                    "status": 200,
                    "message": f"Student {student.name} (NISN: {student.nisn}) berhasil dihapus",
                    "detail": {
                        "student_id": student.user_id,
                        "username": user.username.lower(),
                        "name": student.name,
                        "nisn": student.nisn
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": 404,
                    "message": f"Tidak ditemukan user dengan username {user.username} (User ID: {user.id})"
                }, status=status.HTTP_404_NOT_FOUND)

        elif user.role == "teacher":
            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                # Check if teacher is a wali kelas
                if teacher.homeroomId:
                    return Response({
                        "status": 400,
                        "message": f"Cannot delete teacher {teacher.name} as they are currently assigned as a wali kelas. Please reassign or remove their wali kelas role first."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                teacher.isDeleted = True
                teacher.save()
                return Response({
                    "status": 200,
                    "message": f"Teacher {teacher.name} (NISP: {teacher.nisp}) has been successfully deleted",
                    "detail": {
                        "user_id": user.id,
                        "teacher_id": teacher.user_id,
                        "username": user.username.lower(),
                        "name": teacher.name,
                        "nisp": teacher.nisp,
                        "angkatan" : teacher.angkatan.angkatan if teacher.angkatan else None
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": 404,
                    "message": f"Teacher record not found for user {user.username} (User ID: {user.id})"
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                "status": 400,
                "message": "Cannot delete admin users"
            }, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        return Response({
            "status": 404,
            "message": f"User with ID {id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error deleting user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminRole])
def edit_user(request, id):
    try:
        user = User.objects.get(id=id)
        original_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "isActive" : user.is_active
        }
        
        data = request.data
        updated_fields = []

        if "username" in data and data["username"] != user.username:
            usernamee = data["username"].lower()
            if User.objects.filter(username=usernamee).exclude(id=user.id).exists():
                return Response({
                "status": 400,
                "message": f"Tidak dapat mengubah username user tersebut. Terdapat username {usernamee} dengan username yang sama."
            }, status=status.HTTP_400_BAD_REQUEST)
            updated_fields.append("username")
            user.username = data["username"].lower()
        if "email" in data and data["email"] != user.email:
            updated_fields.append("email")
            user.email = data["email"]
        if "role" in data and data["role"] != user.role:
            return Response({
                "status": 400,
                "message": "Tidak dapat mengubah role user. Silakan hapus user dan buat baru dengan role yang sesuai."
            }, status=status.HTTP_400_BAD_REQUEST)
        print(data)
        if "password" in data:
            print("ini kejalan")
            user.set_password(data['password'])
            updated_fields.append("password")
        if "isActive" in data:
            active_state = data["isActive"]
            active_state = active_state
            print(active_state)
            if active_state == "true" or active_state=="True" or active_state == True:
                updated_fields.append("isActive")
                user.is_active = True
                print("true kejalan")
            elif active_state == "false" or active_state=="False" or active_state == False:
                updated_fields.append("isActive")
                user.is_active = False
                print("false kejalan")
            else:
                return Response({
                        "status": 400,
                        "message": f"isActive: {data['isActive']} Harus berupa true atau false"
                    }, status=status.HTTP_400_BAD_REQUEST)

        if user.role == "student":
            student = Student.objects.filter(user=user).first()
            if student:
                original_data.update({
                    "student_id": student.user_id,
                    "name": student.name,
                    "nisn": student.nisn,
                    "status": "Deleted" if student.isDeleted else "Active",
                    "angkatan": student.angkatan.angkatan if student.angkatan else None
                })
                if "name" in data and data["name"] != student.name:
                    updated_fields.append("name")
                    student.name = data["name"]
                if "nisn" in data and data["nisn"] != student.nisn:
                    if Student.objects.filter(nisn=data["nisn"]).exclude(user_id=user.id).exists():
                        return Response({
                            "status": 400,
                            "message": f"NISN {data['nisn']} sudah digunakan oleh siswa lain"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    updated_fields.append("nisn")
                    student.nisn = data["nisn"]
                if "angkatan" in data and data["angkatan"] != student.angkatan.angkatan:
                    angkatan = data["angkatan"]
                    try:
                        AngkatanObj, created = Angkatan.objects.get_or_create(angkatan=angkatan)
                    except:
                        raise serializers.ValidationError({"status":"400","Message":"Angkatan gagal dibuat!"})
                    updated_fields.append("angkatan")
                    student.angkatan = AngkatanObj
                
                student.save()
            else:
                return Response({
                    "status": 404,
                    "message": f"Student record not found for user {user.username} (User ID: {user.id})"
                }, status=status.HTTP_404_NOT_FOUND)

        elif user.role == "teacher":
            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                original_data.update({
                    "teacher_id": teacher.user_id,
                    "name": teacher.name,
                    "nisp": teacher.nisp,
                    "angkatan":teacher.angkatan.angkatan
                })
                
                if "name" in data and data["name"] != teacher.name:
                    updated_fields.append("name")
                    teacher.name = data["name"]
                if "nisp" in data and data["nisp"] != teacher.nisp:
                    # Check if NISP already exists for another teacher
                    if Teacher.objects.filter(nisp=data["nisp"]).exclude(user_id=user.id).exists():
                        return Response({
                            "status": 400,
                            "message": f"NISP {data['nisp']} sudah digunakan oleh guru lain"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    updated_fields.append("nisp")
                    teacher.nisp = data["nisp"]
                if "angkatan" in data and data["angkatan"] != teacher.angkatan.angkatan:
                    angkatan = data["angkatan"]
                    try:
                        AngkatanObj, created = Angkatan.objects.get_or_create(angkatan=angkatan)
                    except:
                        raise serializers.ValidationError({"status":"400","Message":"Angkatan gagal dibuat!"})
                    updated_fields.append("angkatan")
                    teacher.angkatan = AngkatanObj
                
                teacher.save()
                user.save()
            else:
                return Response({
                    "status": 404,
                    "message": f"Data guru tidak ditemukan untuk username {user.username} (User ID: {user.id})"
                }, status=status.HTTP_404_NOT_FOUND)
        
        user.save()
        if len(updated_fields) == 0:
            print("yessss")
            response_data = {
            "original_data": original_data,
            "updated_fields": "tidak ada (kosong)",
            "current_data": {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
        else:
            response_data = {
                "original_data": original_data,
                "updated_fields": updated_fields,
                "current_data": {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "password":"Password berhasil diganti"
                }
            }
        
        if user.role == "student" and student:
            response_data["current_data"].update({
                "student_id": student.user_id,
                "name": student.name,
                "nisn": student.nisn,
                "angkatan": student.angkatan.angkatan,
                "isActive": user.is_active
            })
        elif user.role == "teacher" and teacher:
            response_data["current_data"].update({
                "teacher_id": teacher.user_id,
                "name": teacher.name,
                "nisp": teacher.nisp,
                "angkatan":teacher.angkatan.angkatan,
                "isActive": user.is_active
            })
        if len(updated_fields) == 0:
               return Response({
                "status": 200,
                "message": f"User berhasil diperbarui (field yang diubah: Tidak ada)",
                "detail": response_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": 200,
                "message": f"User berhasil diperbarui (field yang diubah: {', '.join(updated_fields)})",
                "detail": response_data
            }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            "status": 404,
            "message": f"User with ID {id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error updating user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# End update and delete user
# test commit WKWKKW
# testtt
# List all user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """List all users in the system"""
    users = User.objects.all()
    
    # Create a list to store user data
    user_list = []
    
    for user in users:
        if user.role == 'student':
            try:
                student = Student.objects.get(user=user)
                if student.isDeleted:
                    continue
            except Student.DoesNotExist:
                pass
        elif user.role == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                if teacher.isDeleted:
                    continue
            except Teacher.DoesNotExist:
                pass
        else:
            continue

        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'isActive': user.is_active,
            'createdAt':user.createdAt,
            'updatedAt':user.updatedAt
        }
        if user.role == 'student':
            try:
                student = Student.objects.get(user=user)
                active_classes = student.siswa.filter(isActive=True, isDeleted=False).values_list('namaKelas', flat=True)
                user_data.update({
                    'name': student.name,
                    'angkatan':student.angkatan.angkatan,
                    'isAssignedtoClass':student.isAssignedtoClass,
                    'activeClasses': list(active_classes)
                })
            except Student.DoesNotExist:
                pass
        elif user.role == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                homeroom_class = teacher.homeroomId.namaKelas if teacher.homeroomId and not teacher.homeroomId.isDeleted and teacher.homeroomId.isActive else None
                user_data.update({
                    'name': teacher.name,
                    'angkatan':teacher.angkatan.angkatan,
                    'homeroomClass': homeroom_class
                })
            except Teacher.DoesNotExist:
                pass
        
        user_list.append(user_data)
    
    return Response({
        'status': '200',
        'message': 'Berhasil mendapatkan semua list user',
        'data': user_list
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def student_by_angkatan(request, angkatan):
    try:
        angkatan = int(angkatan)
        if angkatan < 100:  
            angkatan += 2000 
        print(angkatan)
        try:
            print("try")
            angkatanObj, created = Angkatan.objects.get_or_create(angkatan=angkatan)
        except:
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Tidak terdapat angkatan tersebut ({angkatan}) pada sistem."
            }, status=404)

        print(angkatanObj.angkatan)
        print(angkatanObj.id)
        siswa_angkatan= Student.objects.filter(
            isActive=True,
            isDeleted=False,
            angkatan=angkatanObj.id
        )
        print(siswa_angkatan)
        print("heree")
        
        # Ambil siswa yang belum masuk kelas atau hanya masuk kelas yang tidak aktif/dihapus
        # Changed id__in to user_id__in to match the model's field
#
        if not siswa_angkatan.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Tidak ada siswa yang tersedia untuk angkatan {angkatan}."
            }, status=404)

        return JsonResponse({
            "status": 200,
            "message": f"Daftar siswa yang tersedia untuk angkatan {angkatan}",
            "data": [
                {
                    "id": s.user.id,
                    "name": s.name,
                    "isAssignedtoClass": s.isAssignedtoClass,
                    "nisn": s.nisn,
                    "username": s.username,
                    "angkatan": s.angkatan.angkatan
                } for s in siswa_angkatan
            ]
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
