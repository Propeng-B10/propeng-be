from django.db import IntegrityError
from rest_framework import serializers
from .models import MataPelajaran
from user.models import Teacher, Student

class MataPelajaranSerializer(serializers.ModelSerializer):
    namaMatpel = serializers.ChoiceField(choices=MataPelajaran.MATKUL_CHOICES)
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(), required=False, allow_null=True)
    siswa_terdaftar = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), many=True, required=False)

    class Meta:
        model = MataPelajaran
        fields = ['id', 'namaMatpel', 'kode', 'kelas', 'tahun_ajaran', 'teacher', 'siswa_terdaftar', 'is_archived']
        read_only_fields = ['kode']  # Karena kode dibuat otomatis di `save()`

    def validate(self, data):
        """Check for uniqueness of namaMatpel, kelas, and tahun_ajaran"""
        if MataPelajaran.objects.filter(
            namaMatpel=data['namaMatpel'],
            kelas=data['kelas'],
            tahun_ajaran=data['tahun_ajaran']
        ).exists():
            raise serializers.ValidationError({
                "detail": "MataPelajaran with this namaMatpel, kelas, and tahun_ajaran already exists."
            })  # 🔹 Ensure error is formatted correctly for API response

        return data

    def create(self, validated_data):
        try:
            siswa_data = validated_data.pop('siswa_terdaftar', [])  # Extract siswa_terdaftar list

            matapelajaran = MataPelajaran.objects.create(**validated_data)  # Create object first

            if siswa_data:
                matapelajaran.siswa_terdaftar.set(siswa_data)  # Use .set() for ManyToMany

            return matapelajaran
        except:
            raise serializers.ValidationError({
                "detail": "MataPelajaran with this namaMatpel, kelas, and tahun_ajaran already exists."
            })
