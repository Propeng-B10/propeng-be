from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import MataPelajaran, TahunAjaran, Teacher, Student
from .serializers import MataPelajaranSerializer
from user.models import User
from django.db import connection

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_mata_pelajaran(request):
    print("🔹 create_mata_pelajaran 1")
    
    serializer = MataPelajaranSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            matapelajaran = serializer.save()
            return Response({
                "status": 201,
                "message": "Matpel created successfully!",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "status": 400,
                "message": f"Failed to create Mata Pelajaran: {str(e)}",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
            "status": 400,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_matapelajaran(request):
    """List all mata pelajaran, including both archived and active"""
    try:
        matapelajaran = MataPelajaran.objects.filter(isDeleted=False)
        matapelajaran_list = []
        
        for mapel in matapelajaran:
            # Get teacher name if assigned
            teacher_name = mapel.teacher.name if mapel.teacher else None
            
            # Count enrolled students
            student_count = mapel.siswa_terdaftar.count()
            
            mapel_data = {
                "id": mapel.id,
                "nama": mapel.nama,
                "kategoriMatpel": mapel.get_kategoriMatpel_display(),  # Get readable choice name
                "kode": mapel.kode,
                "tahunAjaran": mapel.tahunAjaran.tahunAjaran if mapel.tahunAjaran else None,
                "teacher": {
                    "id": mapel.teacher.user_id if mapel.teacher else None,
                    "name": teacher_name
                },
                "jumlah_siswa": student_count,
                "status": "Active" if mapel.isActive else "Inactive",
                "angkatan":mapel.angkatan.angkatan if mapel.angkatan else None
            }
            matapelajaran_list.append(mapel_data)
            
        return Response({
            "status": 200,
            "message": "Successfully retrieved mata pelajaran list",
            "data": matapelajaran_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving mata pelajaran list: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_mata_pelajaran(request, pk):
    """Update an existing MataPelajaran"""
    try:
        matapelajaran = MataPelajaran.objects.get(pk=pk)
    except MataPelajaran.DoesNotExist:
        return Response({
            "status": 404,
            "message": "MataPelajaran not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Create a copy of the request data
    data = request.data.copy()
    
    # Handle partial updates (PATCH)
    partial = request.method == 'PATCH'
    
    # Process tahunAjaran if provided
    if 'tahunAjaran' in data:
        tahun = data.get('tahunAjaran')
        try:
            tahun_ajaran, created = TahunAjaran.objects.get_or_create(tahunAjaran=tahun)
            # For validation in the serializer
            data['tahunAjaran_instance'] = tahun_ajaran.id
        except Exception as e:
            return Response({
                "status": 400,
                "message": f"Error with TahunAjaran: {str(e)}",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    if 'status' in data:
        if data['status'].lower() == "active":
            data['status'] = True
        elif data['status'].lower() == "inactive":
            data["status"] = False
        print(data)

    
    # Create serializer with the instance and data
    serializer = MataPelajaranSerializer(matapelajaran, data=data, partial=partial)
    
    if serializer.is_valid():
        try:
            updated_matapelajaran = serializer.save()
            return Response({
                "status": 200,
                "message": "MataPelajaran updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "status": 400,
                "message": f"Failed to update MataPelajaran: {str(e)}",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
            "status": 400,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_mata_pelajaran(request, pk):
    """Delete an existing MataPelajaran"""
    try:
        matapelajaran = MataPelajaran.objects.get(pk=pk)
    except MataPelajaran.DoesNotExist:
        return Response({
            "status": 404,
            "message": "MataPelajaran not found"
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        # Store information for response before deletion
        matapelajaran_info = {
            "id": matapelajaran.id,
            "nama": matapelajaran.nama,
            "angkatan": matapelajaran.angkatan.id if matapelajaran.angkatan else None, 
            "kategoriMatpel": matapelajaran.get_kategoriMatpel_display(),
            "tahunAjaran": matapelajaran.tahunAjaran.tahunAjaran if matapelajaran.tahunAjaran else None
        }

        # Soft-delete the MataPelajaran
        matapelajaran.isDeleted = True
        matapelajaran.save()

        # Return success response with deleted item info
        return Response({
            "status": 200,
            "message": "MataPelajaran deleted successfully",
            "deleted_item": matapelajaran_info
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "status": 400,
            "message": f"Failed to delete MataPelajaran: {str(e)}",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mata_pelajaran_by_id(request, pk):
    """Retrieve a specific MataPelajaran by ID"""
    try:
        matapelajaran = MataPelajaran.objects.get(pk=pk)
    except MataPelajaran.DoesNotExist:
        return Response({
            "status": 404,
            "message": "MataPelajaran not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        teacher_name = matapelajaran.teacher.name if matapelajaran.teacher else None
        student_count = matapelajaran.siswa_terdaftar.count()

        # Retrieve students
        siswa_terdaftar_list = [
            {
                "id": student.user_id,
                "name": student.name,
                "username": student.username
            } for student in matapelajaran.siswa_terdaftar.all()
        ]
        
        matapelajaran_data = {
            "id": matapelajaran.id,
            "nama": matapelajaran.nama,
            "kategoriMatpel": matapelajaran.get_kategoriMatpel_display(),
            "kode": matapelajaran.kode,
            "tahunAjaran": matapelajaran.tahunAjaran.tahunAjaran if matapelajaran.tahunAjaran else None,
            "teacher": {
                "id": matapelajaran.teacher.user_id if matapelajaran.teacher else None,
                "name": teacher_name
            },
            "jumlah_siswa": student_count,
            "siswa_terdaftar": siswa_terdaftar_list,
            "angkatan": matapelajaran.angkatan.angkatan if matapelajaran.angkatan else None
        }

        
        return Response({
            "status": 200,
            "message": "Successfully retrieved MataPelajaran",
            "data": matapelajaran_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving MataPelajaran: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)