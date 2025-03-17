from django.http import JsonResponse
from rest_framework.decorators import api_view
from kelas.models import Kelas
from kelas.models import Student
from kelas.models import Teacher
from tahunajaran.models import TahunAjaran
import re

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

        # Ambil semua siswa di angkatan tersebut
        siswa_list = Student.objects.filter(angkatan=angkatan)

        # Ambil siswa yang sudah masuk dalam kelas
        siswa_tanpa_kelas = siswa_list.filter(isAssignedtoClass=False)

        if not siswa_tanpa_kelas.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Tidak ada siswa tanpa kelas untuk angkatan {angkatan}."
            }, status=404)

        return JsonResponse({
            "status": 200,
            "message": f"Daftar siswa yang belum memiliki kelas untuk angkatan {angkatan}",
            "data": [
                {
                    "id": s.user.id,
                    "name": s.name,
                    "isAssignedtoClass": s.isAssignedtoClass,
                    "nisn": s.nisn,
                    "username": s.username,
                    "angkatan": s.angkatan
                } for s in siswa_tanpa_kelas
            ]
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
    
@api_view(['GET'])
def list_available_homeroom(request):
    """List all teachers, including both active and deleted, and show teachers without homeroom"""
    try:
        # Filter guru yang tidak menjadi wali kelas (homeroomId is NULL)
        teachers_without_homeroom = Teacher.objects.filter(homeroomId__isnull=True)

        if not teachers_without_homeroom.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": "Tidak ada guru yang tidak menjadi wali kelas."
            }, status=404)

        teacher_list = []
        for teacher in teachers_without_homeroom:
            teacher_data = {
                "id": teacher.user_id,
                "name": teacher.name,
                "username": teacher.user.username,  # Synchronized username
                "nisp": teacher.nisp,
                "status": "Deleted" if teacher.isDeleted else "Active"
            }
            teacher_list.append(teacher_data)
            
        return JsonResponse({
            "status": 200,
            "message": "Daftar guru yang tidak menjadi wali kelas",
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

        waliKelas = Teacher.objects.get(user_id=wali_kelas_id)

        # **Cek apakah wali kelas sudah memiliki homeroomId di kelas aktif lain**
        if Kelas.objects.filter(waliKelas=waliKelas, isActive=True).exists():
            return JsonResponse({
                "status": 400,
                "errorMessage": "Wali kelas ini sudah terdaftar di kelas lain."
            }, status=400)

        # **RESET homeroomId jika tidak cocok dengan kelas aktif mana pun**
        if waliKelas.homeroomId and not Kelas.objects.filter(id=waliKelas.homeroomId.id, isActive=True).exists():
            waliKelas.homeroomId = None
            waliKelas.save()

        if not nama_kelas:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Nama kelas wajib diisi."
            }, status=400)

        # **Cek apakah semua siswa ditemukan**
        siswa_list = Student.objects.filter(user_id__in=siswa_ids)
        found_siswa_ids = set(siswa_list.values_list('user_id', flat=True))
        missing_siswa_ids = set(siswa_ids) - found_siswa_ids

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
                "isActive": kelas.isActive
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
    isEmpty = False

    # Buat ambil keseluruhannya
    kelas = Kelas.objects.all().order_by('-isActive', '-updatedAt')

    if not kelas.exists():
        isEmpty = True

        ''' Ini pertama ngecek isEmpty dulu, 
        nah kalau True artinya gak ada kan, terus bisa store Error Message di FE-nya '''
        return JsonResponse({
                # "isEmpty":isEmpty,
                "status": 400,
                "errorMessage": "Belum ada kelas yang terdaftar! Silahkan menambahkan kelas baru."
            }, status = 400)


    ''' Ini pertama ngecek isEmpty dulu, 
    nah kalau False baru deh ambil data.json dari "data" '''
    return JsonResponse({
            # "isEmpty":isEmpty,
            "status": 201,
            "message": "Semua kelas berhasil diambil!",
            "data": [
                {
                    "id": k.id,
                    "namaKelas": re.sub(r'^Kelas\s+', '', k.namaKelas, flags=re.IGNORECASE) if k.namaKelas else None,
                    "tahunAjaran": k.tahunAjaran.tahunAjaran if k.tahunAjaran else None,
                    "waliKelas": str(k.waliKelas) if k.waliKelas else None,
                    "totalSiswa": k.siswa.count(),
                    "angkatan": k.angkatan if k.angkatan >= 1000 else k.angkatan + 2000,
                    "isActive": k.isActive,
                    "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "isAssignedtoClass": s.isAssignedtoClass,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in k.siswa.all()
                ]}for k in kelas
                

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
            "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
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
            "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
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
            "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
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

        # Simpan wali kelas sebelumnya sebelum perubahan
        wali_kelas_sebelumnya = kelas.waliKelas

        if wali_kelas_id and Kelas.objects.filter(isActive=True, waliKelas_id=wali_kelas_id).exclude(id=kelas_id).exists():
            return JsonResponse({"status": 400, "errorMessage": "Wali kelas sudah mengajar di kelas lain yang masih aktif!"}, status=400)

        if wali_kelas_id is not None:
            if kelas.waliKelas_id:
                Teacher.objects.filter(user_id=kelas.waliKelas).update(homeroomId=None)
            Teacher.objects.filter(user_id=wali_kelas_id).update(homeroomId=kelas.id)

        if wali_kelas_id is None and kelas.waliKelas:
            Teacher.objects.filter(user_id=kelas.waliKelas).update(homeroomId=None)

        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": "Wali kelas berhasil diubah!",
            "data": {
                "idKelas": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "idWaliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
                "namaWaliKelas": f"{kelas.waliKelas.name}" if kelas.waliKelas else None,
                "idWaliKelasSebelumnya": str(wali_kelas_sebelumnya) if wali_kelas_sebelumnya else None,
                "namaWaliKelasSebelumnya": str(wali_kelas_sebelumnya.name) if wali_kelas_sebelumnya else None
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": 500, "errorMessage": f"Terjadi kesalahan saat mengupdate kelas: {str(e)}"}, status=500)

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

'''
[PBI 12] Menghapus Kelas (Soft Delete)
'''
@api_view(['DELETE'])
def delete_kelas(request, kelas_id):
    try:
        # Ambil kelas berdasarkan ID
        kelas = Kelas.objects.get(id=kelas_id)

        # Set isActive menjadi False (Soft Delete)
        kelas.isActive = False

        # Set isAssignedtoClass = False untuk semua siswa dalam kelas ini
        kelas.siswa.update(isAssignedtoClass=False)

        wali_kelas = kelas.waliKelas
        if wali_kelas and wali_kelas.homeroomId == kelas.id:
            wali_kelas.homeroomId = None
        wali_kelas.save()

        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": f"Kelas {kelas.namaKelas} berhasil dinonaktifkan."
        }, status=200)

    except Kelas.DoesNotExist:
        return JsonResponse({
            "status": 400,
            "errorMessage": "Kelas tidak ditemukan."
        }, status=400)
