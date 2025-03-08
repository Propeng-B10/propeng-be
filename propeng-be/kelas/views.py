from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from kelas.models import Kelas
from user.models import Teacher

'''
[PBI 9] Menambahkan Kelas
'''
@api_view(['CREATE'])
def create_kelas(request):
    return

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

    return JsonResponse({

        ''' Ini pertama ngecek isEmpty dulu, 
        nah kalau False baru deh ambil data.json dari "data" '''

            "isEmpty":isEmpty,
            "status": 200,
            "data": [
                {
                "id": k.id,
                "nama": k.namaKelas ,
                "tahunAjaran": f"T.A. {k.tahunAjaran}/{k.tahunAjaran+1}",
                "statusKelas": k.isActive,
                "waliKelas": k.waliKelas,
                "totalSiswa": k.siswa.count(),
                } for k in kelas
            ],
        }, status = 200)


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
        
        return JsonResponse({
                "isEmpty":isEmptyClass,
                "isEmptySiswainClass":isEmptySiswainClass,
                "status": 200,
                "id": kelas.id,
                "nama": kelas.namaKelas,
                "tahunAjaran": f"T.A. {kelas.tahunAjaran}/{kelas.tahunAjaran+1}",
                "statusKelas": kelas.isActive,
                "waliKelas": f"{kelas.waliKelas.name} (NISP: {kelas.waliKelas.nisp})" if kelas.waliKelas else "Belum ada wali kelas",
                "totalSiswa": kelas.siswa.count(),
                "data": [
                    {
                        "idSiswa" : s.id,
                        "nama" : s.name,
                        "username" : s.username,
                        "nisn" : s.nisn,
                    } for s in siswa
                ],
            }, status = 200)
    
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
@api_view(['PUT','PATCH'])
def update_kelas(request):
    return

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
