from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from kelas.models import Kelas
from kelas.models import Student
from kelas.models import Teacher
from tahunajaran.models import TahunAjaran

'''
[PBI 9] Menambahkan Kelas
'''
# Mengambil yang dipilih dari sekian list guru, murid
@api_view(['POST'])
def create_kelas(request):
    # Mengambil 'body' nya
    try: 
        data = request.data
        nama_kelas = data.get("namaKelas")
        wali_kelas_id = data.get("waliKelas")
        students_id = data.get("students",[])
        tahun_ajaran_id = data.get("tahunAjaran")


        # Memastikan wali kelas ada di db
        try:
            wali_kelas = Teacher.objects.get(id=wali_kelas_id)
        except Teacher.DoesNotExist:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Wali kelas tidak ditemukan"
            }, status=400)
        
        # Memastikan tahun ajaran ada di db
        try:
            tahun_ajaran = TahunAjaran.objects.get(tahunAjaran=tahun_ajaran_id)
        except TahunAjaran.DoesNotExist:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tahun ajaran tidak ditemukan"
            }, status=400)
        
        # Memastikan wali kelas belum masuk kelas manapun
        if Kelas.objects.filter(isActive=True, waliKelas=wali_kelas).exists():
            return JsonResponse({
                "status": 400,
                "errorMessage": "Wali kelas sudah masuk ke suatu kelas"
            }, status=400)
        

        # Ambil daftar siswa dari database
        existing_students = Student.objects.filter(id__in=students_id)

        # Memastikan murid belum masuk kelas lain
        students_in_active_classes = Kelas.objects.filter(
            isActive=True, siswa__in=existing_students
        ).values_list("siswa__id", flat=True)

        students_already_in_class = set(students_id) & set(students_in_active_classes)

        if students_already_in_class:
            return JsonResponse({
                "status": 400,
                "errorMessage": f"Siswa dengan ID {list(students_already_in_class)} sudah terdaftar di kelas lain!"
            }, status=400)

        # Buat objek kelas
        kelas = Kelas.objects.create(
            namaKelas=nama_kelas,
            waliKelas=wali_kelas,
            tahunAjaran=tahun_ajaran 
        )

        # Tambahkan siswa ke dalam kelas
        kelas.siswa.set(existing_students)

        return JsonResponse({
            "status": 201,
            "message": "Kelas berhasil dibuat!",
            "data": {
                "id": kelas.id,
                "namaKelas": kelas.namaKelas,
                "tahunAjaran": f"T.A. {kelas.tahunAjaran.tahunAjaran}/{kelas.tahunAjaran.tahunAjaran+1}",
                "waliKelas": f"{kelas.waliKelas} (NISP: {kelas.waliKelas.nisp})",
                "totalSiswa": kelas.siswa.count(),
                "siswa": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username,
                        "tahunAjaran": s.tahunAjaran.tahunAjaran,
                        "createdAt": s.createdAt,
                        "updatedAt": s.updatedAt
                    } for s in kelas.siswa.all()
                ]
            }
        }, status=201)
    
    except Exception:
        return JsonResponse(
            {"status":500, "errorMessage":"Terjadi kesalahan saat membuat kelas"}
        )

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
                "namaKelas": k.namaKelas,
                "tahunAjaran": f"T.A. {k.tahunAjaran.tahunAjaran}/{k.tahunAjaran.tahunAjaran+1}",
                "waliKelas": f"{k.waliKelas} (NISP: {k.waliKelas.nisp})",
                "totalSiswa": k.siswa.count(),
                "siswa": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username,
                        "tahunAjaran": s.tahunAjaran.tahunAjaran,
                        "createdAt": s.createdAt,
                        "updatedAt": s.updatedAt
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
    try:
        # Ambil berdasarkan id kelas
        kelas = Kelas.objects.get(id=kelas_id)
        siswa = kelas.siswa.all()

        if not siswa.exists():
            isEmptySiswainClass = True
            return JsonResponse({
                "isEmptySiswainClass":isEmptySiswainClass,
                "status": 400,
                "errorMessage": "Tidak ada siswa di kelas ini. Silakan kembali."
            }, status = 400) 
        
        return JsonResponse(
            {
            "isEmpty":isEmptyClass,
            "isEmptySiswainClass":isEmptySiswainClass,
            "status": 201,
            "message": "Kelas yang dicari ada",
            "id": kelas.id,
            "namaKelas": kelas.namaKelas,
            "tahunAjaran": f"T.A. {kelas.tahunAjaran.tahunAjaran}/{kelas.tahunAjaran.tahunAjaran+1}",
            "waliKelas": f"{kelas.waliKelas} (NISP: {kelas.waliKelas.nisp})",
            "totalSiswa": kelas.siswa.count(),
            "siswa": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username,
                        # "tahunAjaran": s.tahunAjaran.tahunAjaran,
                        # "createdAt": s.createdAt,
                        # "updatedAt": s.updatedAt
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

        # Update data kelas jika ada perubahan
        if nama_kelas:
            kelas.namaKelas = nama_kelas
        if wali_kelas_id:
            kelas.waliKelas_id = wali_kelas_id
        if tahun_ajaran:
            kelas.tahunAjaran = tahun_ajaran
        if students_id:
            kelas.siswa.set(existing_students)

        kelas.save()

        return JsonResponse({
            "status": 200,
            "message": "Kelas berhasil diperbarui!",
            "data": {
                "id": kelas.id,
                "namaKelas": kelas.namaKelas,
                "tahunAjaran": f"T.A. {kelas.tahunAjaran}/{kelas.tahunAjaran+1}",
                "waliKelas": f"{kelas.waliKelas} (NISP: {kelas.waliKelas.nisp})",
                "totalSiswa": kelas.siswa.count(),
                "siswa": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "nisn": s.nisn,
                        "username": s.username,
                        "tahunAjaran": s.tahunAjaran,
                        "createdAt": s.createdAt.isoformat(),
                        "updatedAt": s.updatedAt.isoformat(),
                    } for s in kelas.siswa.all()
                ]
            }
        }, status=200)

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
