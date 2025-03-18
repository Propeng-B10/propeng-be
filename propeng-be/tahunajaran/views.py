from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Angkatan
from .serializers import AngkatanSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_angkatan(request):
    """API untuk mengambil daftar angkatan"""
    try:
        angkatan_list = Angkatan.objects.all()
        serializer = AngkatanSerializer(angkatan_list, many=True)
        
        return Response({
            "status": 200,
            "message": "Successfully retrieved angkatan list",
            "data": serializer.data
        }, status=200)

    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving angkatan list: {str(e)}"
        }, status=500)
