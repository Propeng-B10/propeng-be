from rest_framework import serializers
from .models import Angkatan

class AngkatanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Angkatan
        fields = ["id", "angkatan"]  # ✅ Hanya ambil field yang diperlukan
