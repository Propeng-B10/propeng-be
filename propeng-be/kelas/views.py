from datetime import timedelta
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from kelas.models import Kelas
from kelas.models import Student
from kelas.models import Teacher
from matapelajaran.models import MataPelajaran
from tahunajaran.models import TahunAjaran
import re
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Q  
from tahunajaran.models import Angkatan
from absensi.models import *


class IsTeacherRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'teacher')

'''
Cek Siswa Tertentu pada Suatu Angkatan
'''

@api_view(['GET'])
def list_available_student_by_angkatan(request, angkatan):
    """List students who are NOT assigned to any class for a given batch"""
    try:
        # Normalisasi angkatan (misal: 23 → 2023, 2023 → tetap 2023)
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
        siswa_dalam_kelas_yang_ga_aktif = Student.objects.filter(
            isActive=True,
            isDeleted=False,
            angkatan=angkatanObj.id,
            isAssignedtoClass=False
        )
        print(siswa_dalam_kelas_yang_ga_aktif)
        print("heree")
        
        # Ambil siswa yang belum masuk kelas atau hanya masuk kelas yang tidak aktif/dihapus
        # Changed id__in to user_id__in to match the model's field
#
        if not siswa_dalam_kelas_yang_ga_aktif.exists():
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
                } for s in siswa_dalam_kelas_yang_ga_aktif
            ]
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

@api_view(['POST'])
def add_siswa_to_kelas(request, kelas_id):
    try:
        data = request.data
        students_id = data.get("students", [])  # List of student IDs
        angkatan = data.get("angkatan")

        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Kelas tidak ditemukan!"}, status=404)

        if not students_id:
            return JsonResponse({"status": 400, "errorMessage": "Tidak ada siswa yang dikirimkan!"}, status=400)

        students_name = []
        for i in students_id:
            studentTemp = Student.objects.get(user_id=i)
            studentTemp.isAssignedtoClass = True
            kelas.siswa.add(studentTemp.user_id)
            students_name.append(studentTemp)

        # Update isAssignedtoClass flag for all students in this class
        for student in kelas.siswa.all():
            student.isAssignedtoClass = True
            student.save()


        return JsonResponse({
            "status": 200,
            "message": f"Siswa berhasil ditambahkan ke kelas!",
            "data": {
                "kelasId": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "siswa": [
                    {"id": s.user.id, "name": s.name, "nisn": s.nisn, "username": s.username, "angkatan": s.angkatan.angkatan, "isAssignedtoClass": s.isAssignedtoClass}
                    for s in students_name
                ]
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat menambahkan siswa ke kelas: {str(e)}"}, status=500)


@api_view(['GET'])
def list_available_homeroom(request):
    """List all teachers, including both active and deleted, and show teachers without homeroom"""
    try:
        # Get teachers with no homeroom assignment
        teachers_without_homeroom = Teacher.objects.filter(homeroomId__isnull=True)
        
        # Get teachers whose homeroom is deleted or inactive
        teachers_with_inactive_homeroom = Teacher.objects.filter(
            Q(homeroomId__isDeleted=True) | 
            Q(homeroomId__isActive=False)
        )
        
        # Combine the two querysets
        available_teachers = (teachers_without_homeroom | teachers_with_inactive_homeroom).distinct()

        # Debug: Print the SQL query being executed
        print(available_teachers.query)
        
        # Debug: Check if Mira Susanti exists in the database
        mira = Teacher.objects.filter(name__icontains='Mira Susanti').first()
        if mira:
            print(f"Mira found: {mira.name}, homeroomId: {mira.homeroomId}")
        
        if not available_teachers.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": "Tidak ada guru yang tersedia untuk menjadi wali kelas."
            }, status=404)
        # test commit
    
        teacher_list = []
        for teacher in available_teachers:
            teacher_data = {
                "id": teacher.user_id,
                "name": teacher.name,
                "username": teacher.user.username,
                "nisp": teacher.nisp,
                "status": "Deleted" if teacher.isDeleted else "Active",
                "currentHomeroom": str(teacher.homeroomId.namaKelas) if teacher.homeroomId else None,
                "currentHomeroomStatus": {
                    "isActive": teacher.homeroomId.isActive if teacher.homeroomId else None,
                    "isDeleted": teacher.homeroomId.isDeleted if teacher.homeroomId else None
                } if teacher.homeroomId else None
            }
            teacher_list.append(teacher_data)
            
        return JsonResponse({
            "status": 200,
            "message": "Daftar guru yang tersedia untuk menjadi wali kelas",
            "data": teacher_list
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

@api_view(['GET'])
def list_all_homeroom(request):
    try:
        homerooms = Kelas.objects.filter(isActive=True).select_related('tahunAjaran', 'waliKelas').prefetch_related('siswa')

        data = []
        for k in homerooms:
            data.append({
                "id": k.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', k.namaKelas, flags=re.IGNORECASE) if k.namaKelas else None,
                "tahunAjaran": f"{k.tahunAjaran.tahunAjaran}" if k.tahunAjaran else None,
                "waliKelas": f"{k.waliKelas}" if k.waliKelas else None,
                "totalSiswa": k.siswa.count(),
                "angkatan": k.angkatan,
                "isActive": k.isActive
            })

        return JsonResponse({
            "status": 200,
            "message": "Daftar homeroom berhasil diambil.",
            "data": data
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
    
'''
[PBI 9] Menambahkan Kelas
'''
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import TahunAjaran, Teacher, Student, Kelas

@api_view(['POST'])
def create_kelas(request):
    try:
        data = request.data
        nama_kelas = data.get('namaKelas')
        tahun_ajaran_id = data.get('tahunAjaran')
        wali_kelas_id = data.get('waliKelas')
        angkatan = data.get('angkatan')
        siswa_ids = data.get('siswa', [])

        # **Hapus prefix "Kelas " jika ada di awal nama_kelas**
        nama_kelas = re.sub(r'^Kelas\s+', '', nama_kelas, flags=re.IGNORECASE)

        tahun_ajaran, created = TahunAjaran.objects.get_or_create(
            tahunAjaran=tahun_ajaran_id
        )
        print(wali_kelas_id)
        waliKelas = Teacher.objects.get(user_id=wali_kelas_id)
        print(wali_kelas_id)
        # FIXED: Check if this teacher is assigned as waliKelas in any active, non-deleted class
        if Kelas.objects.filter(waliKelas=waliKelas, isActive=True, isDeleted=False).exists():
            return JsonResponse({
                "status": 400,
                "errorMessage": "Wali kelas ini sudah terdaftar di kelas lain."
            }, status=400)

        # **RESET homeroomId jika tidak cocok dengan kelas aktif mana pun**
        print("gagal disisni")
        if waliKelas.homeroomId and (waliKelas.homeroomId.isDeleted or not waliKelas.homeroomId.isActive):
            waliKelas.homeroomId = None
            waliKelas.save()
        print("gagal dahh")
        if not nama_kelas:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Nama kelas wajib diisi."
            }, status=400)

        # **Cek apakah semua siswa ditemukan**
        siswa_list = Student.objects.filter(user_id__in=siswa_ids)
        found_siswa_ids = set(siswa_list.values_list('user_id', flat=True))
        missing_siswa_ids = set(siswa_ids) - found_siswa_ids
        print("kokk")
        if missing_siswa_ids:
            return JsonResponse({
                "status": 400,
                "errorMessage": f"Siswa dengan user_id {list(missing_siswa_ids)} tidak ditemukan."
            }, status=400)

        # Normalisasi angkatan agar selalu dalam format 4 digit (2023, 2025, dst.)
        if angkatan < 100:
            angkatan += 2000  # Ubah 23 -> 2023, 25 -> 2025
        
        # **Membuat kelas**
        kelas = Kelas.objects.create(
            namaKelas=nama_kelas,
            tahunAjaran=tahun_ajaran,
            waliKelas=waliKelas,
            angkatan=angkatan,
            isActive=True
        )
        print(kelas.isActive)
        kelas.isActive = True
        kelas.save()
        print(kelas.isActive)
        kelas.siswa.set(siswa_list)
        # Update siswa yang masuk ke kelas baru sebagai `isAssignedtoClass = True`
        Student.objects.filter(user_id__in=siswa_ids).update(isAssignedtoClass=True)

        waliKelas.homeroomId = kelas
        waliKelas.save()

        return JsonResponse({
            "status": 201,
            "message": "Kelas berhasil dibuat!",
            "data": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "tahunAjaran": f"{kelas.tahunAjaran.tahunAjaran}" if kelas.tahunAjaran else None,
                "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
                "totalSiswa": kelas.siswa.count(),
                "angkatan": kelas.angkatan,
                "isActive": kelas.isActive,
                "createdAt": kelas.createdAt.strftime("%d-%m-%Y %H:%M:%S") if kelas.createdAt else None,
                "updatedAt": kelas.updatedAt.strftime("%d-%m-%Y %H:%M:%S") if kelas.createdAt else None
            }
        }, status=201)
    except Teacher.DoesNotExist:
        return JsonResponse({
            "status": 400,
            "errorMessage": "Wali kelas tidak ditemukan."
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)


'''
[PBI 10] Melihat Kelas: List Kelas
'''
@api_view(['GET'])
def list_kelas(request):
    # Only get non-deleted classes
    kelas = Kelas.objects.filter(isDeleted=False).order_by('-isActive', '-updatedAt')
    
    if not kelas.exists():
        return JsonResponse({
            "status": 404,
            "errorMessage": "Belum ada kelas yang terdaftar! Silahkan menambahkan kelas baru."
        }, status=400)

    return JsonResponse({
        "status": 201,
        "message": "Semua kelas berhasil diambil!",
        "data": [
            {
                "id": k.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', k.namaKelas, flags=re.IGNORECASE) if k.namaKelas else None,
                "tahunAjaran": k.tahunAjaran.tahunAjaran if k.tahunAjaran else None,
                "waliKelas": k.waliKelas.name if k.waliKelas else None,
                "totalSiswa": k.siswa.count(),
                "angkatan": k.angkatan if k.angkatan >= 1000 else k.angkatan + 2000,
                "isActive": k.isActive,
                "expiredAt": k.expiredAt.strftime('%Y-%m-%d') if k.expiredAt else None,
                "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in k.siswa.all()
                ]
            } for k in kelas
        ]
    }, status=201)

'''
[PBI 10] Melihat Kelas: Detail Kelas
'''
@api_view(['GET'])
def detail_kelas(request, kelas_id):
    isEmptyClass = False
    isEmptySiswainClass = False
    isEmptyWaliKelasinClass = False
    try:
        # Ambil berdasarkan id kelas
        kelas = Kelas.objects.get(id=kelas_id)
        siswa = kelas.siswa.all()
        waliKelas = kelas.waliKelas

        teacher_name = waliKelas.name if waliKelas else None
        print(teacher_name)

        if not waliKelas:
            isEmptySiswainClass = False
            return JsonResponse({
            # "isEmpty":isEmptyClass,
            # "isEmptySiswainClass":isEmptySiswainClass,
            "status": 201,
            "message": "Tidak ada wali kelas di kelas ini",
            "id": kelas.id,
            "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
            "tahunAjaran": f"{kelas.tahunAjaran.tahunAjaran}" if kelas.tahunAjaran else None,
            "waliKelas": teacher_name,
            "totalSiswa": kelas.siswa.count(),
            "isActive": kelas.isActive,
            "angkatan": kelas.angkatan if kelas.angkatan >= 1000 else kelas.angkatan + 2000,
            "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in kelas.siswa.all()
                ]
            })
        
        if not siswa.exists():
            isEmptySiswainClass = True
            isEmptyWaliKelasinClass = False
            return JsonResponse({
            # "isEmpty":isEmptyClass,
            # "isEmptySiswainClass":isEmptySiswainClass,
            # "isEmptyWaliKelasinClass":isEmptyWaliKelasinClass,
            "status": 201,
            "message": "Tidak ada siswa di kelas ini",
            "id": kelas.id,
            "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
            "tahunAjaran": f"{kelas.tahunAjaran.tahunAjaran}" if kelas.tahunAjaran else None,
            "waliKelas": teacher_name,
            "totalSiswa": kelas.siswa.count(),
            "isActive": kelas.isActive,
            "angkatan": kelas.angkatan if kelas.angkatan >= 1000 else kelas.angkatan + 2000,
            "siswa": [
                    {
                        "id": s.user.id,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in kelas.siswa.all()
                ]
            })
        
        return JsonResponse(
            {
            # "isEmpty":isEmptyClass,
            # "isEmptySiswainClass":isEmptySiswainClass,
            # "isEmptyWaliKelasinClass":isEmptyWaliKelasinClass,
            "status": 201,
            "message": "Kelas yang dicari ada",
            "id": kelas.id,
            "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
            "tahunAjaran": f"{kelas.tahunAjaran.tahunAjaran}" if kelas.tahunAjaran else None,
            "waliKelas": teacher_name,
            "totalSiswa": kelas.siswa.count(),
            "isActive": kelas.isActive,
            "angkatan": kelas.angkatan if kelas.angkatan >= 1000 else kelas.angkatan + 2000,
            "siswa": [
                    {
                        "id": s.user.id,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in kelas.siswa.all()
                ]
            }
            )
    
    except Kelas.DoesNotExist:
        isEmptyClass = True
        return JsonResponse({
                "isEmpty":isEmptyClass,
                "status": 400,
                "errorMessage": "Tidak ada kelas ini. Silakan kembali."
            }, status = 400)
    

'''
[PBI 11] Mengubah Informasi Kelas
'''

@api_view(['PUT', 'PATCH'])
def update_nama_kelas(request, kelas_id):
    try:
        data = request.data
        nama_kelas = data.get("namaKelas")

        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Kelas tidak ditemukan!"}, status=404)


        # Simpan nama kelas sebelumnya sebelum diubah
        nama_kelas_sebelumnya = kelas.namaKelas

        # Update data kelas
        kelas.namaKelas = nama_kelas if nama_kelas is not None else kelas.namaKelas
        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": "Nama kelas berhasil diubah!",
            "data": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "namaKelasSebelumnya": re.sub(r'^Kelas\s+', '', nama_kelas_sebelumnya, flags=re.IGNORECASE) if nama_kelas_sebelumnya else None,
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat mengupdate nama kelas: {str(e)}"}, status=500)

@api_view(['PUT', 'PATCH'])
def update_wali_kelas(request, kelas_id):
    try:
        data = request.data
        wali_kelas_id = data.get("waliKelas")

        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Kelas tidak ditemukan!"}, status=404)

        # Save previous homeroom teacher
        previous_wali_kelas = kelas.waliKelas

        # If there's a previous homeroom teacher, clear their assignment
        if previous_wali_kelas:
            previous_teacher = Teacher.objects.get(user_id=previous_wali_kelas.user_id)
            previous_teacher.homeroomId = None
            previous_teacher.save()

        # If a new homeroom teacher is specified
        if wali_kelas_id:
            try:
                new_teacher = Teacher.objects.get(user_id=wali_kelas_id)
                
                # Check if the new teacher is already assigned to another active class
                if new_teacher.homeroomId and new_teacher.homeroomId.id != kelas_id and new_teacher.homeroomId.isActive and not new_teacher.homeroomId.isDeleted:
                    return JsonResponse({"status": 400, "errorMessage": "Guru ini sudah menjadi wali kelas di kelas lain!"}, status=400)
                
                kelas.waliKelas = new_teacher
                new_teacher.homeroomId = kelas
                new_teacher.save()
            except Teacher.DoesNotExist:
                return JsonResponse({"status": 404, "errorMessage": "Guru tidak ditemukan!"}, status=404)
        else:
            kelas.waliKelas = None

        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": "Wali kelas berhasil diubah!",
            "data": {
                "idKelas": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                "previousWaliKelas": previous_wali_kelas.name if previous_wali_kelas else None
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat mengupdate wali kelas: {str(e)}"}, status=500)

@api_view(['PUT', 'PATCH'])
def update_kelas(request, kelas_id):
    try:
        data = request.data
        nama_kelas = data.get("namaKelas")
        wali_kelas_id = data.get("waliKelas")
        students_id = data.get("students", [])
        tahun_ajaran = data.get("tahunAjaran")

        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Kelas tidak ditemukan!"}, status=404)

        if wali_kelas_id and Kelas.objects.filter(isActive=True, waliKelas_id=wali_kelas_id).exclude(id=kelas_id).exists():
            return JsonResponse({"status": 400, "errorMessage": "Wali kelas sudah mengajar di kelas lain yang masih aktif!"}, status=400)

        if students_id:
            existing_students = Student.objects.filter(user_id__in=students_id)
            students_in_active_classes = set(Kelas.objects.filter(isActive=True, siswa__in=existing_students)
                                             .exclude(id=kelas_id)
                                             .values_list("siswa__user_id", flat=True))
            students_already_in_class = set(students_id) & students_in_active_classes
            if students_already_in_class:
                return JsonResponse({"status": 400, "errorMessage": f"Siswa dengan ID {list(students_already_in_class)} sudah masuk ke kelas lain yang masih aktif!"}, status=400)

        if wali_kelas_id is not None:
            if kelas.waliKelas_id:
                Teacher.objects.filter(user_id=kelas.waliKelas).update(homeroomId=None)
            Teacher.objects.filter(user_id=wali_kelas_id).update(homeroomId=kelas.id)

        if wali_kelas_id is None and kelas.waliKelas:
            Teacher.objects.filter(user_id=kelas.waliKelas).update(homeroomId=None)

        
        # Update data kelas
        kelas.namaKelas = nama_kelas if nama_kelas is not None else kelas.namaKelas
        kelas.waliKelas_id = wali_kelas_id if wali_kelas_id is not None else kelas.waliKelas_id

        if tahun_ajaran is not None:
            kelas.tahunAjaran, _ = TahunAjaran.objects.get_or_create(tahunAjaran=tahun_ajaran) if tahun_ajaran else (None, False)

        if students_id:
            # Set siswa yang tidak ada dalam daftar baru ke isAssignedtoClass=False
            removed_students = kelas.siswa.exclude(user_id__in=students_id)
            removed_students.update(isAssignedtoClass=False)

            # Update daftar siswa dalam kelas
            kelas.siswa.set(existing_students)
            existing_students.update(isAssignedtoClass=True)

        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": "Kelas berhasil diubah!",
            "data": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "tahunAjaran": f"{kelas.tahunAjaran.tahunAjaran}" if kelas.tahunAjaran else None,
                "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
                "totalSiswa": kelas.siswa.count(),
                "isActive": kelas.isActive,
                "angkatan": kelas.angkatan if kelas.angkatan >= 1000 else kelas.angkatan + 2000,
                "siswa": [
                    {"id": s.user.id, "name": s.name, "nisn": s.nisn, "username": s.username, "isAssignedtoClass": s.isAssignedtoClass,}
                    for s in kelas.siswa.all()
                ]
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat mengupdate kelas: {str(e)}"}, status=500)

@api_view(['DELETE'])
def delete_siswa_from_kelas(request, kelas_id, siswa_id):
    try:
        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Kelas tidak ditemukan!"}, status=404)

        try:
            siswa = Student.objects.get(user_id=siswa_id)
        except Student.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Siswa tidak ditemukan!"}, status=404)

        # Check if student is in the class
        if not kelas.siswa.filter(user_id=siswa_id).exists():
            return JsonResponse({"status": 404, "errorMessage": "Siswa tidak ditemukan dalam kelas ini!"}, status=404)

        # Simpan data siswa sebelum dihapus
        siswa_sebelumnya = {
            "id": siswa.user_id,
            "name": siswa.name,
            "nisn": siswa.nisn if hasattr(siswa, 'nisn') else "",
            "username": siswa.username if hasattr(siswa, 'username') else "",
            "isAssignedtoClass": siswa.isAssignedtoClass if hasattr(siswa, 'isAssignedtoClass') else False,
        }

        # Remove student from class
        kelas.siswa.remove(siswa)
        
        # Update student status
        siswa.isAssignedtoClass = False
        siswa.save()

        return JsonResponse({
            "status": 200,
            "message": "Siswa berhasil dihapus dari kelas!",
            "data": {
                "kelasId": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "siswaSebelumnya": siswa_sebelumnya
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat menghapus siswa dari kelas: {str(e)}"}, status=500)

'''
[PBI 12] Menghapus Kelas (Soft Delete)
'''
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_multiple_kelas(request):
    try:
        data = request.data
        # 1 2 3 4
        # 3 4 --> absen --> gabisa delete
        class_ids = data.get('class_ids', [])
        
        if not class_ids:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada kelas yang dipilih untuk dihapus."
            }, status=400)
        
        # Get all classes to be deleted
        classes = Kelas.objects.filter(id__in=class_ids)
        
        if not classes.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan."
            }, status=404)
        
        deleted_count = 0
        for kelas in classes:
            # Set isDeleted to True (Soft Delete)
            undeleted_classes = []
            if AbsensiHarian.objects.filter(kelas=kelas.id).count() != 0:
                undeleted_classes.append(kelas.namaKelas)
                continue
                

            kelas.isDeleted = True
            
            # Set isAssignedtoClass = False for all students in this class
            students = kelas.siswa.all()
            for student in students:
                student.isAssignedtoClass = False
                student.save()
            
            # Update homeroom teacher
            wali_kelas = kelas.waliKelas
            if wali_kelas and wali_kelas.homeroomId and wali_kelas.homeroomId.id == kelas.id:
                print(f"Before: Teacher {wali_kelas.name} has homeroomId {wali_kelas.homeroomId}")
                wali_kelas.homeroomId = None
                wali_kelas.save()
                print(f"After: Teacher {wali_kelas.name} has homeroomId {wali_kelas.homeroomId}")
            
            kelas.save()
            deleted_count += 1
        undeleted_classes
        if len(undeleted_classes) == 0:
            return JsonResponse({
                "status": 200,
                "message": f"{deleted_count} kelas berhasil dihapus (soft delete).",
                "deletedCount": deleted_count
            }, status=200)
        else:
            return JsonResponse({
                "status": 200,
                "message": f"{deleted_count} kelas berhasil dihapus terkecuali kelas {undeleted_classes}.",
                "deletedCount": deleted_count
            }, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_kode_absensi_kelas(request, kelas_id):
    try:
        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({"status": 404, "errorMessage": "Kelas tidak ditemukan!"}, status=404)
        kode= ""
        if not kelas.isActive:
            return JsonResponse({"status": 404, "errorMessage": "Kelas sudah tidak aktif!"}, status=404)
        if kelas.kode is None or kelas.kode_is_expired():
            kode = kelas.generate_kode()
        else:
            kode = kelas.kode
        print(kode)
        print(kelas.kode_expiry_time)
        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": "Kode berhasil didapatkan!",
            "data": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "kode": f"{kelas.kode}" if kelas.kode else kode
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat membuat Kode kelas: {str(e)}"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kelas_with_absensi(request):
    try:
        semua_kelas = Kelas.objects.all()
        print(semua_kelas)
        
        if len(semua_kelas) == 0:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Belum ada kelas yang tersedia."
            }, status=400)
        kelas_ada_absensi = {}
        for kelas in semua_kelas:
            # Set isDeleted to True (Soft Delete)
            print(kelas.id)
            print(kelas.namaKelas)
            print(AbsensiHarian.objects.filter(kelas=kelas.id))
            if AbsensiHarian.objects.filter(kelas=kelas).exists():
                print("disini ke run")
                data_kelas = []
                data_kelas.append(f"ID Kelas : {kelas.id}")
                data_kelas.append(f"Nama Kelas : {kelas.namaKelas}")
                print(data_kelas)
                kelas_ada_absensi[kelas.id] = (data_kelas)
                print(kelas_ada_absensi)
            print("disini abis if")
        print("disini abis for loop")
        print(kelas_ada_absensi)
        if len(kelas_ada_absensi) == 0:
            return JsonResponse({
                "status": 200,
                "message": f"Tidak terdapat kelas yang memiliki absen",
                "kelasYangMemilikiAbsen": kelas_ada_absensi
            }, status=200)
        else:
            return JsonResponse({
                "status": 200,
                "message": f"List kelas yang memiliki Absensi berhasil didapatkan.",
                "kelasYangMemilikiAbsen": kelas_ada_absensi
            }, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_teacher_kelas(request):
    """
    Return only the classes where the current teacher is assigned as homeroom teacher
    and that are currently active
    """
    try:
        # Get the current teacher user
        current_user = request.user
        
        # Find the teacher object for the current user
        try:
            teacher = Teacher.objects.get(user_id=current_user.id)
        except Teacher.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Data guru tidak ditemukan untuk user ini."
            }, status=404)
        
        # Get all active classes where this teacher is the homeroom teacher
        teacher_classes = Kelas.objects.filter(
            waliKelas=teacher,
            isActive=True,
            isDeleted=False
        ).order_by('-updatedAt')
        
        if not teacher_classes.exists():
            return JsonResponse({
                "status": 404,
                "message": "Anda tidak menjadi wali kelas untuk kelas aktif manapun saat ini."
            }, status=404)
        
        # Format the response with classes and attendance statistics
        response_data = []
        for k in teacher_classes:
            # Get the total count of students
            total_students = k.siswa.count()
            
            # Initialize attendance counters
            total_alfa = 0
            total_hadir = 0
            total_sakit = 0
            total_izin = 0
            
            # Get the most recent absensi record for this class if it exists
            latest_absensi = AbsensiHarian.objects.filter(kelas=k).order_by('-date').first()
            
            if latest_absensi:
                # Count attendance statuses
                for student_id, data in latest_absensi.listSiswa.items():
                    if isinstance(data, dict):
                        status = data.get("status", "")
                    else:
                        status = data
                    
                    if status == "Alfa":
                        total_alfa += 1
                    elif status == "Hadir":
                        total_hadir += 1
                    elif status == "Sakit":
                        total_sakit += 1
                    elif status == "Izin":
                        total_izin += 1
            
             # Ambil semua siswa di kelas
            siswa_kelas = k.siswa.all()

            print(k.siswa.all())

            # Cari semua matpel yang siswanya ada dalam kelas ini
            matpel_qs = MataPelajaran.objects.filter(
                siswa_terdaftar__in=siswa_kelas,
                isDeleted=False,
                isActive=True,
            ).distinct()

            print(matpel_qs)

            # Siapkan list matpel unik
            mata_pelajaran_unik = [
                {
                    "id": mp.id,
                    "nama": mp.nama,
                    "kode": mp.kode,
                    "kategori": mp.kategoriMatpel,
                }
                for mp in matpel_qs
            ]

            
            # Add class data with attendance stats to response
            response_data.append({
                "id": k.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', k.namaKelas, flags=re.IGNORECASE) if k.namaKelas else None,
                "tahunAjaran": k.tahunAjaran.tahunAjaran if k.tahunAjaran else None,
                "waliKelas": k.waliKelas.name if k.waliKelas else None,
                "totalSiswa": total_students,
                "absensiStats": {
                    "totalAlfa": total_alfa,
                    "totalHadir": total_hadir,
                    "totalSakit": total_sakit,
                    "totalIzin": total_izin
                },
                "mata_pelajaran_unik": mata_pelajaran_unik, 
                "angkatan": k.angkatan if k.angkatan >= 1000 else k.angkatan + 2000,
                "isActive": k.isActive,
                "expiredAt": k.expiredAt.strftime('%Y-%m-%d') if k.expiredAt else None,
                "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in k.siswa.all()
                ]
            })
        
        return JsonResponse({
            "status": 200,
            "message": "Daftar kelas yang Anda menjadi wali kelas",
            "data": response_data
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_teacher_all_kelas(request):
    """
    Return only the classes where the current teacher is assigned as homeroom teacher
    and that are currently active
    """
    try:
        # Get the current teacher user
        current_user = request.user
        
        # Find the teacher object for the current user
        try:
            teacher = Teacher.objects.get(user_id=current_user.id)
        except Teacher.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Data guru tidak ditemukan untuk user ini."
            }, status=404)
        
        # Get all active classes where this teacher is the homeroom teacher
        teacher_classes = Kelas.objects.filter(
            waliKelas=teacher,
            isDeleted=False
        ).order_by('-updatedAt')
        
        if not teacher_classes.exists():
            return JsonResponse({
                "status": 404,
                "message": "Anda tidak menjadi wali kelas untuk kelas aktif manapun saat ini."
            }, status=404)
        
        # Format the response with classes and attendance statistics
        response_data = []
        for k in teacher_classes:
            # Get the total count of students
            total_students = k.siswa.count()

            # Add class data with attendance stats to response
            response_data.append({
                "id": k.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', k.namaKelas, flags=re.IGNORECASE) if k.namaKelas else None,
                "tahunAjaran": k.tahunAjaran.tahunAjaran if k.tahunAjaran else None,
                "waliKelas": k.waliKelas.name if k.waliKelas else None,
                "totalSiswa": total_students,
                "angkatan": k.angkatan if k.angkatan >= 1000 else k.angkatan + 2000,
                "isActive": k.isActive,
                "expiredAt": k.expiredAt.strftime('%Y-%m-%d') if k.expiredAt else None,
            })
        
        return JsonResponse({
            "status": 200,
            "message": "Daftar kelas yang Anda menjadi wali kelas",
            "data": response_data
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_detail_kelas_baru(request, kelas_id):
    try:
        teacher_classes = Kelas.objects.filter(id=kelas_id)
        response_data = []
        for k in teacher_classes:
            # Get the total count of students
            total_students = k.siswa.count()
            
            # Initialize attendance counters
            total_alfa = 0
            total_hadir = 0
            total_sakit = 0
            total_izin = 0
            
            # Get the most recent absensi record for this class if it exists
            latest_absensi = AbsensiHarian.objects.filter(kelas=k).order_by('-date').first()
            
            if latest_absensi:
                # Count attendance statuses
                for student_id, data in latest_absensi.listSiswa.items():
                    if isinstance(data, dict):
                        status = data.get("status", "")
                    else:
                        status = data
                    
                    if status == "Alfa":
                        total_alfa += 1
                    elif status == "Hadir":
                        total_hadir += 1
                    elif status == "Sakit":
                        total_sakit += 1
                    elif status == "Izin":
                        total_izin += 1
            
             # Ambil semua siswa di kelas
            siswa_kelas = k.siswa.all()

            print(k.siswa.all())

            # Cari semua matpel yang siswanya ada dalam kelas ini
            matpel_qs = MataPelajaran.objects.filter(
                siswa_terdaftar__in=siswa_kelas,
                isDeleted=False,
                isActive=True,
            ).distinct()

            print(matpel_qs)

            # Siapkan list matpel unik
            mata_pelajaran_unik = [
                {
                    "id": mp.id,
                    "nama": mp.nama,
                    "kode": mp.kode,
                    "kategori": mp.kategoriMatpel,
                }
                for mp in matpel_qs
            ]

            
            # Add class data with attendance stats to response
            response_data.append({
                "id": k.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', k.namaKelas, flags=re.IGNORECASE) if k.namaKelas else None,
                "tahunAjaran": k.tahunAjaran.tahunAjaran if k.tahunAjaran else None,
                "waliKelas": k.waliKelas.name if k.waliKelas else None,
                "totalSiswa": total_students,
                "absensiStats": {
                    "totalAlfa": total_alfa,
                    "totalHadir": total_hadir,
                    "totalSakit": total_sakit,
                    "totalIzin": total_izin
                },
                "mata_pelajaran_unik": mata_pelajaran_unik, 
                "angkatan": k.angkatan if k.angkatan >= 1000 else k.angkatan + 2000,
                "isActive": k.isActive,
                "expiredAt": k.expiredAt.strftime('%Y-%m-%d') if k.expiredAt else None,
                "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in k.siswa.all()
                ]
            })
        
        return JsonResponse({
            "status": 200,
            "message": "Daftar kelas yang Anda menjadi wali kelas",
            "data": response_data
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)