from django.http import JsonResponse
from django.shortcuts import render
from .models import *
from kelas.models import *
from rest_framework.decorators import api_view, permission_classes
import re
from rest_framework.permissions import IsAuthenticated
# Create your views here.

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

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def list_absen_id(request, idKelas):
#     kelas = Kelas.objects.filter(id=idKelas)
#     absen = AbsensiHarian.objects.filter(kelas=idKelas)
    
#     if not absen.exists():
#         return JsonResponse({
#             "status": 404,
#             "errorMessage": "Belum ada absen yang terdaftar! Silahkan buat absen baru."
#         }, status=400)

#     return JsonResponse({
#         "status": 201,
#         "message": "Semua absen berhasil diambil!",
#         "data": [
#             {
#                 "id": k.id,
#                 "kelas": k.kelas.namaKelas,
#                 "teacher":k.kelas.waliKelas.name,
#                 "absensiHari":k.date,
#                 "data" : k.listSiswa
#             } for k in absen
#         ]
#     }, status=201)