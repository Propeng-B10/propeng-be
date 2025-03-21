from rest_framework import serializers
from .models import Nilai
from user.models import User
from matapelajaran.models import MataPelajaran

class NilaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nilai
        fields = ['id', 'matapelajaran', 'student', 'jenis_nilai', 'nilai', 'keterangan', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        # Validate that the student exists
        try:
            student = User.objects.get(pk=data['student'].id)
            if student.role != 'student':
                raise serializers.ValidationError("Selected user is not a student")
        except User.DoesNotExist:
            raise serializers.ValidationError("Selected student does not exist")

        # Validate that the mata pelajaran exists
        try:
            matapelajaran = MataPelajaran.objects.get(pk=data['matapelajaran'].id)
        except MataPelajaran.DoesNotExist:
            raise serializers.ValidationError("Selected mata pelajaran does not exist")

        # Validate that the student is enrolled in the mata pelajaran
        if not matapelajaran.siswa_terdaftar.filter(user_id=student.id).exists():
            raise serializers.ValidationError("Student is not enrolled in this mata pelajaran")

        # Validate nilai range (0-100)
        if data['nilai'] < 0 or data['nilai'] > 100:
            raise serializers.ValidationError("Nilai must be between 0 and 100")

        return data 