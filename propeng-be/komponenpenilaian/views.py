from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import MataPelajaran, KomponenPenilaian
from .serializers import KomponenPenilaianSerializer
from django.db.models import ProtectedError

"""
PBI 24 - Menambahkan Komponen Penilaian pada Mata Pelajaran

API untuk menambahkan komponen penilaian pada
mata pelajaran terkait.
"""
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_komponen_penilaian(request):
    serializer = KomponenPenilaianSerializer(data=request.data)
    if serializer.is_valid():
        try:
            komponenPenilaian = serializer.save()
            return Response({
                "status": 201,
                "message": f"Komponen Penilaian dengan ID {komponenPenilaian.id} berhasil dibuat!",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "status": 400,
                "message": f"Gagal membuat Komponen Penilaian: {str(e)}",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
            "status": 400,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
"""
PBI 25 - Melihat Komponen Penilaian pada Mata Pelajaran

API untuk mengembalikan komponen penilaian pada
mata pelajaran terkait.
"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_komponen_penilaian(request):
    komponenList = KomponenPenilaian.objects.all()
    serializer = KomponenPenilaianSerializer(komponenList, many=True)
    return Response({
        "status": 200,
        "message": "Berhasil mengambil semua Komponen Penilaian.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_komponen_penilaian_of_mata_pelajaran(request):
    mataPelajaranId = request.query_params.get("id")
    
    if not mataPelajaranId:
        return Response({
            "status": 400,
            "message": "Parameter mataPelajaranId wajib diisi.",
            "error": "Query parameter mataPelajaranId is required."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        mataPelajaranObj = MataPelajaran.objects.get(pk=mataPelajaranId)
    except MataPelajaran.DoesNotExist:
        return Response({
            "status": 404,
            "message": f"Mata Pelajaran dengan ID {mataPelajaranId} tidak ditemukan.",
            "error": f"Mata Pelajaran dengan ID {mataPelajaranId} tidak ditemukan."
        }, status=status.HTTP_404_NOT_FOUND)

    komponenList = KomponenPenilaian.objects.filter(mataPelajaran=mataPelajaranObj)
    serializer = KomponenPenilaianSerializer(komponenList, many=True)

    return Response({
        "status": 200,
        "message": f"Berhasil mengambil Komponen Penilaian untuk Mata Pelajaran ID {mataPelajaranId}",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_komponen_penilaian_by_id(request):
    komponenPenilaianId = request.query_params.get("id")
    
    if not komponenPenilaianId:
        return Response({
            "status": 400,
            "message": "Parameter komponenPenilaianId wajib diisi.",
            "error": "Query parameter komponenPenilaianId is required."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        komponen = KomponenPenilaian.objects.get(pk=komponenPenilaianId)
    except KomponenPenilaian.DoesNotExist:
        return Response({
            "status": 404,
            "message": f"Komponen Penilaian dengan ID {komponenPenilaianId} tidak ditemukan.",
            "error": f"Komponen Penilaian dengan ID {komponenPenilaianId} tidak ditemukan."
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = KomponenPenilaianSerializer(komponen)
    return Response({
        "status": 200,
        "message": f"Berhasil mengambil Komponen Penilaian dengan ID {komponenPenilaianId}",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

"""
PBI 26 - Mengubah Informasi Komponen Penilaian pada Mata Pelajaran

API untuk mengubah detail informasi komponen penilaian.
"""
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_komponen_penilaian(request, pk):
    try:
        komponen = KomponenPenilaian.objects.get(pk=pk)
    except KomponenPenilaian.DoesNotExist:
        return Response(
            {
                "status": 404,
                "message": f"Komponen Penilaian dengan ID {pk} tidak ditemukan.",
                "error": f"Komponen Penilaian dengan ID {pk} tidak ditemukan."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = KomponenPenilaianSerializer(komponen, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 200,
            "message": f"Berhasil memperbarui Komponen Penilaian dengan ID {pk}.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    return Response({
        "status": 400,
        "message": "Gagal memperbarui Komponen Penilaian.",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

"""
PBI 27 - Menghapus Komponen Penilaian pada Mata Pelajaran

API untuk menghapus suatu komponen penilaian.
"""
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_komponen_penilaian(request, pk):
    try:
        komponen = KomponenPenilaian.objects.get(pk=pk)
    except KomponenPenilaian.DoesNotExist:
        return Response(
            {
                "status": 404,
                "message": f"Komponen Penilaian dengan ID {pk} tidak ditemukan.",
                "error": f"Komponen Penilaian dengan ID {pk} tidak ditemukan."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        komponen.delete()
        return Response(
            {
                "status": 200,
                "message": f"Berhasil menghapus Komponen Penilaian dengan ID {pk}."
            },
            status=status.HTTP_200_OK
        )
    except ProtectedError:
        return Response(
            {
                "status": 400,
                "message": f"Gagal menghapus Komponen Penilaian karena masih memiliki relasi dengan data nilai.",
                "error": "Data masih terhubung ke nilai."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
