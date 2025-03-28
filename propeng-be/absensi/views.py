from django.http import JsonResponse
from django.shortcuts import render
from .models import *
from kelas.models import *
from rest_framework.decorators import api_view, permission_classes
import re
from rest_framework.permissions import IsAuthenticated, BasePermission
# Create your views here.

class IsStudentRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_absen(request):
    absen = AbsensiHarian.objects.all()
    
    if not absen.exists():
        return JsonResponse({
            "status": 404,
            "errorMessage": "Belum ada absen yang terdaftar! Silahkan buat absen baru."
        }, status=400)

    return JsonResponse({
        "status": 201,
        "message": "Semua absen berhasil diambil!",
        "data": [
            {
                "id": k.id,
                "kelas": k.kelas.namaKelas,
                "teacher":k.kelas.waliKelas.name,
                "absensiHari":k.date,
                "data" : k.listSiswa
            } for k in absen
        ]
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentRole])
def absen(request):
    try:
        data = request.data
        id_kelas = data.get('idKelas')
        id_siswa = data.get('idSiswa')
        kode_absen = data.get('kodeAbsen')
        print(data)
        print(id_kelas)
        print(id_siswa)
        print(kode_absen)
        if not id_kelas:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada ID kelas yang dikirimkan. 'idKelas'"
            }, status=400)
        if not id_siswa:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada ID siswa yang dikirimkan. 'idSiswa'"
            }, status=400)
        if not kode_absen:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada kode absen yang dikirimkan. 'kodeAbsen'"
            }, status=400)
        print("why")
        # Get all classes to be deleted    
        kelas = Kelas.objects.get(id=id_kelas)
        student = Student.objects.get(user_id=id_siswa)
        print(kelas)
        print(student)
        if not kelas:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan."
            }, status=404)
        if not student:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan."
            }, status=404)
        print("here")
        absensi = AbsensiHarian.objects.get(kelas_id=kelas.id)
        print("this")
        if kelas.check_kode(kode_absen) == "Berhasil":
            print("tutor")
            status = absensi.update_absen("Hadir", id_siswa)
            print("jkkk")
        elif kelas.check_kode() == "Gagal":
            print("disini")
            return JsonResponse({
            "status": 400,
            "message": f"Kode yang kamu submit salah."
            }, status=200)
        if status!="Berhasil":
            return JsonResponse({
            "status": 400,
            "message": f"Terdapat permasalahan pada saat mengupdate data atas nama {student.name} untuk kelas {kelas.namaKelas}."
            }, status=200)
        return JsonResponse({
            "status": 200,
            "message": f"Siswa atas nama {student.name} berhasil absen untuk kelas {kelas.namaKelas}."
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)