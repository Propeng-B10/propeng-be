from rest_framework import serializers
from .models import Nilai
from user.models import User
from matapelajaran.models import MataPelajaran

class NilaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nilai
        fields = ['id', 'matapelajaran', 'student', 'nilai', 'keterangan', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        student = data.get('student')
        matapelajaran = data.get('matapelajaran')

        if not student or not matapelajaran:
            raise serializers.ValidationError("Both student and matapelajaran must be provided")

        if student.role != 'student':
            raise serializers.ValidationError("Selected user is not a student")

        if not matapelajaran.siswa_terdaftar.filter(user_id=student.id).exists():
            raise serializers.ValidationError("Student is not enrolled in this mata pelajaran")

        if data['nilai'] < 0 or data['nilai'] > 100:
            raise serializers.ValidationError("Nilai must be between 0 and 100")

        # Prevent duplicate nilai for the same student and matapelajaran
        if self.instance is None and Nilai.objects.filter(
            student=student,
            matapelajaran=matapelajaran,
        ).exists():
            raise serializers.ValidationError("Nilai for this student and mata pelajaran already exists")

        return data
