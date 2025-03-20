from rest_framework import serializers
from .models import Nilai
from user.models import Student
from matapelajaran.models import MataPelajaran

class NilaiSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    mata_pelajaran_name = serializers.CharField(source='mata_pelajaran.nama', read_only=True)
    
    class Meta:
        model = Nilai
        fields = ['id', 'student', 'student_name', 'mata_pelajaran', 'mata_pelajaran_name', 'nilai', 'createdAt', 'updatedAt']
        read_only_fields = ['createdAt', 'updatedAt']

    def validate(self, data):
        # Check if student exists and is not deleted
        try:
            student = Student.objects.get(user_id=data['student'].user_id)
            if student.isDeleted:
                raise serializers.ValidationError(f"Student {student.name} is deleted")
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student does not exist")

        # Check if mata_pelajaran exists and is not deleted
        try:
            matapelajaran = MataPelajaran.objects.get(id=data['mata_pelajaran'].id)
            if matapelajaran.isDeleted:
                raise serializers.ValidationError(f"Mata Pelajaran {matapelajaran.nama} is deleted")
        except MataPelajaran.DoesNotExist:
            raise serializers.ValidationError("Mata Pelajaran does not exist")

        # Check if student is enrolled in the mata_pelajaran
        if not matapelajaran.siswa_terdaftar.filter(user_id=student.user_id).exists():
            raise serializers.ValidationError(f"Student {student.name} is not enrolled in {matapelajaran.nama}")

        return data 