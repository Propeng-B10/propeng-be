from django.db import models
from user.models import Teacher, Student 
from matapelajaran.models import MataPelajaran


class EvalGuru(models.Model):
    pilihanvariabel = [
        1, 2, 3, 4, 5
    ]
    pilihanindikator = [
        1, 2, 3, 4, 5
    ]
    pilihanskorlikert = [
        1, 2, 3, 4, 5
    ]
    guru = models.ForeignKey(
        Teacher,
        related_name='guru',
        on_delete=models.CASCADE)
    matapelajaran = models.ForeignKey(
        MataPelajaran,
        related_name='matapelajaran',
        on_delete=models.CASCADE)
    siswa = models.ForeignKey(
        Student,
        related_name='siswa',
        on_delete=models.CASCADE)
    variabel = models.PositiveIntegerField(choices=pilihanvariabel)
    indikator = models.PositiveIntegerField(choices=pilihanindikator)
    skorlikert = models.PositiveIntegerField(choices=pilihanskorlikert)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)