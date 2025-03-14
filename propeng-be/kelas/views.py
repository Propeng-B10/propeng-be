from django.http import JsonResponse
from rest_framework.decorators import api_view
from kelas.models import Kelas
from kelas.models import Student
from kelas.models import Teacher
from tahunajaran.models import TahunAjaran


'''
Cek Siswa Tertentu pada Suatu Angkatan
'''
@api_view(['GET'])
def list_siswa_by_angkatan(request, angkatan):
    try:
        # Normalize angkatan (misal: 22 -> 2022, 2022 -> 22)
        angkatan = int(angkatan)
        if angkatan < 100:  
            angkatan += 2000  

        # Filter siswa berdasarkan angkatan
        siswa_list = Student.objects.filter(angkatan=angkatan)

        if not siswa_list.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Tidak ada siswa untuk angkatan {angkatan}."
            }, status=404)

        return JsonResponse({
            "status": 200,
            "message": f"Daftar siswa untuk angkatan {angkatan}",
            "data": [
                {
                    "id": s.user.id,
                    "name": s.name,
                    "nisn": s.nisn,
                    "username": s.username,
                    "angkatan": s.angkatan
                } for s in siswa_list
            ]
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
    
'''
[PBI 9] Menambahkan Kelas
'''
@api_view(['POST'])
def create_kelas(request):
    try:
        data = request.data
        nama_kelas = data.get('namaKelas')
        tahun_ajaran_id = data.get('tahunAjaran')
        wali_kelas_id = data.get('waliKelas')
        angkatan = data.get('angkatan')
        siswa_ids = data.get('siswa', [])

        tahun_ajaran, created = TahunAjaran.objects.get_or_create(
            tahunAjaran=tahun_ajaran_id
        )

        waliKelas=Teacher.objects.get(user_id=wali_kelas_id)

        # **RESET homeroomId jika tidak cocok dengan kelas aktif mana pun**
        if waliKelas.homeroomId and not Kelas.objects.filter(id=waliKelas.homeroomId, isActive=True).exists():
            waliKelas.homeroomId = None
            waliKelas.save()

        if not nama_kelas:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Nama kelas wajib diisi."
            }, status=400)

        kelas = Kelas.objects.create(
            namaKelas=nama_kelas,
            tahunAjaran=tahun_ajaran,
            waliKelas=Teacher.objects.get(user_id=wali_kelas_id),
            angkatan=angkatan,
            isActive=True
        )

        siswa_list = Student.objects.filter(user_id__in=siswa_ids)
        kelas.siswa.set(siswa_list)
        waliKelas.homeroomId = kelas.id
        waliKelas.save()

        return JsonResponse({
            "status": 201,
            "message": "Kelas berhasil dibuat!",
            "data": {
                "id": kelas.id,
                "namaKelas": kelas.namaKelas,
                "tahunAjaran": f"T.A. 20{kelas.tahunAjaran.tahunAjaran}/20{kelas.tahunAjaran.tahunAjaran+1}" if kelas.tahunAjaran else None,
                "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
                "totalSiswa": kelas.siswa.count(),
                "angkatan": kelas.angkatan,
                "isActive": kelas.isActive
            }
        }, status=201)
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
                "isEmpty":isEmpty,
                "status": 400,
                "errorMessage": "Belum ada kelas yang terdaftar! Silahkan menambahkan kelas baru."
            }, status = 400)

    ''' Ini pertama ngecek isEmpty dulu, 
    nah kalau False baru deh ambil data.json dari "data" '''
    return JsonResponse({
            "isEmpty":isEmpty,
            "status": 201,
            "message": "Semua kelas berhasil diambil!",
            "data": [
                {
                "id": k.id,
                "namaKelas": k.namaKelas if k.namaKelas else None,
                "tahunAjaran": f"T.A. 20{k.tahunAjaran.tahunAjaran}/20{k.tahunAjaran.tahunAjaran+1}"  if k.tahunAjaran else None,
                "waliKelas": f"{k.waliKelas}" if k.waliKelas else None,
                "totalSiswa": k.siswa.count(),
                "angkatan": k.angkatan,
                "isActive": k.isActive,
                "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in k.siswa.all()
                ]
                } for k in kelas.all()
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
            "isEmpty":isEmptyClass,
            "isEmptySiswainClass":isEmptySiswainClass,
            "status": 201,
            "message": "Tidak ada wali kelas di kelas ini",
            "id": kelas.id,
            "namaKelas": kelas.namaKelas if kelas.namaKelas!="" else None,
            "tahunAjaran": (f"T.A. 20{kelas.tahunAjaran.tahunAjaran}/20{kelas.tahunAjaran.tahunAjaran+1}"
                            if kelas.tahunAjaran else None
            ),
            "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
            "totalSiswa": kelas.siswa.count(),
            "isActive": kelas.isActive,
            "angkatan": kelas.angkatan,
            "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in kelas.siswa.all()
                ]
            })
        
        if not siswa.exists():
            isEmptySiswainClass = True
            isEmptyWaliKelasinClass = False
            return JsonResponse({
            "isEmpty":isEmptyClass,
            "isEmptySiswainClass":isEmptySiswainClass,
            "isEmptyWaliKelasinClass":isEmptyWaliKelasinClass,
            "status": 201,
            "message": "Tidak ada siswa di kelas ini",
            "id": kelas.id,
            "namaKelas": kelas.namaKelas if kelas.namaKelas!="" else None,
            "tahunAjaran": (f"T.A. 20{kelas.tahunAjaran.tahunAjaran}/20{kelas.tahunAjaran.tahunAjaran+1}"
                            if kelas.tahunAjaran else None
            ),
            "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
            "totalSiswa": kelas.siswa.count(),
            "isActive": kelas.isActive,
            "angkatan": kelas.angkatan,
            "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username
                    } for s in kelas.siswa.all()
                ]
            })
        
        return JsonResponse(
            {
            "isEmpty":isEmptyClass,
            "isEmptySiswainClass":isEmptySiswainClass,
            "isEmptyWaliKelasinClass":isEmptyWaliKelasinClass,
            "status": 201,
            "message": "Kelas yang dicari ada",
            "id": kelas.id,
            "namaKelas": kelas.namaKelas if kelas.namaKelas!="" else None,
            "tahunAjaran": (f"T.A. 20{kelas.tahunAjaran.tahunAjaran}/20{kelas.tahunAjaran.tahunAjaran+1}"
                            if kelas.tahunAjaran else None
            ),
            "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
            "totalSiswa": kelas.siswa.count(),
            "isActive": kelas.isActive,
            "angkatan": kelas.angkatan,
            "siswa": [
                    {
                        "id": s.user.id,
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
def update_kelas(request, kelas_id):
    try:
        # Ambil data dari request
        data = request.data
        nama_kelas = data.get("namaKelas")
        wali_kelas_id = data.get("waliKelas")
        students_id = data.get("students", [])
        tahun_ajaran = data.get("tahunAjaran")

        # Pastikan kelas yang ingin diupdate ada
        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan!"
            }, status=404)

        # Memastikan wali kelas hanya ada di satu kelas aktif
        if wali_kelas_id and Kelas.objects.filter(isActive=True, waliKelas_id=wali_kelas_id).exclude(id=kelas_id).exists():
            return JsonResponse({
                "status": 400,
                "errorMessage": "Wali kelas sudah mengajar di kelas lain yang masih aktif!"
            }, status=400)

        # Memastikan apakah siswa sudah masuk kelas lain yang masih aktif
        existing_students = Student.objects.filter(id__in=students_id)
        students_in_active_classes = set(
            Kelas.objects.filter(isActive=True, siswa__in=existing_students)
            .exclude(id=kelas_id)
            .values_list("siswa__id", flat=True)
        )

        students_already_in_class = set(students_id) & students_in_active_classes

        if students_already_in_class:
            return JsonResponse({
                "status": 400,
                "errorMessage": f"Siswa dengan ID {list(students_already_in_class)} sudah masuk ke kelas lain yang masih aktif!"
            }, status=400)

        # Update homeroomId di model Teacher
        if wali_kelas_id is not None:
            Teacher.objects.filter(id=wali_kelas_id).update(homeroomId=kelas.id)

        # Kalau wali kelas dihapus dari kelas, homeroomId-nya juga dihapus
        if wali_kelas_id is None and kelas.waliKelas:
            Teacher.objects.filter(id=kelas.waliKelas_id).update(homeroomId=None)

        # Update data kelas jika ada perubahan
        if nama_kelas is not None:
            kelas.namaKelas = nama_kelas
        if wali_kelas_id is not None:
            kelas.waliKelas_id = wali_kelas_id
        if tahun_ajaran is not None:
            if tahun_ajaran:  # Jika tidak kosong, cari instance TahunAjaran
                try:
                    tahun_ajaran_instance, _ = TahunAjaran.objects.get_or_create(
                        tahunAjaran=tahun_ajaran
                    )
                    kelas.tahunAjaran = tahun_ajaran_instance
                except TahunAjaran.DoesNotExist:
                    return JsonResponse({
                        "status": 400,
                        "errorMessage": "Tahun ajaran tidak ditemukan!"
                    }, status=400)
            else:  
                kelas.tahunAjaran = None  # Jika null, hapus tahun ajaran
        if students_id is not None:
            kelas.siswa.set(existing_students)

        kelas.save()

        return JsonResponse({
            "status": 201,
            "message": "Kelas berhasil diubah!",
            "data": {
                "id": kelas.id,
                "namaKelas": kelas.namaKelas if kelas.namaKelas!="" else None,
                "tahunAjaran": (f"T.A. 20{kelas.tahunAjaran.tahunAjaran}/20{kelas.tahunAjaran.tahunAjaran+1}"
                                if kelas.tahunAjaran else None
                ),
                "waliKelas": f"{kelas.waliKelas}" if kelas.waliKelas else None,
                "totalSiswa": kelas.siswa.count(),
                "isActive": kelas.isActive,
                "angkatan": kelas.angkatan,
                "siswa": [
                    {
                        "id": s.user.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username,
                    } for s in kelas.siswa.all()
                ]
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan saat mengupdate kelas: {str(e)}"
        }, status=500)

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
