from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import MataPelajaran, TahunAjaran
from .serializers import MataPelajaranSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_mata_pelajaran(request):

    tahun_ajaran, created = TahunAjaran.objects.get_or_create(
    tahunAjaran=request.data["tahunAjaran"])
    request.data["tahunAjaran"] = tahun_ajaran.id 

    serializer = MataPelajaranSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
                    {"status":201,"message": "Matpel created successfully!", "Data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response({"status":200,"message": "Unsuccessful!","error": serializer.errors})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_mata_pelajaran(request):
    """Mengambil Semua MataPelajaran"""
    mata_pelajaran = MataPelajaran.objects.all()
    serializer = MataPelajaranSerializer(mata_pelajaran, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_mata_pelajaran(request, pk):
    """Memodifikasi MataPelajaran"""
    try:
        mata_pelajaran = MataPelajaran.objects.get(pk=pk)
    except MataPelajaran.DoesNotExist:
        return Response({"status":404,"message": "MataPelajaran not found"}, status=status.HTTP_404_NOT_FOUND)

    tahun_ajaran, created = TahunAjaran.objects.get_or_create(
        tahunAjaran=request.data["tahunAjaran"])
    request.data["tahunAjaran"] = tahun_ajaran.id 
        
    serializer = MataPelajaranSerializer(mata_pelajaran, data=request.data, partial=True)  # partial=True agar tidak wajib semua field dikirim
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_mata_pelajaran(request, pk):
    """Menghapus MataPelajaran"""
    try:
        mata_pelajaran = MataPelajaran.objects.get(pk=pk)
    except MataPelajaran.DoesNotExist:
        return Response({"status":404,"error": "MataPelajaran not found"}, status=status.HTTP_404_NOT_FOUND)

    mata_pelajaran.delete()
    return Response({"status":404,"message": "MataPelajaran deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
