from django.db import models
from user.models import Teacher, Student 
from matapelajaran.models import MataPelajaran

# Form evaluasi guru yang diisi oleh siswa 
# Ini gua gatau sih staticnya gimana jadi gua nge-state 1-5
# ~ ini brrt ga nyimpen textnya kan ya
class EvalGuru(models.Model):
    id = models.AutoField(primary_key=True)

    # variabel
    pilihanvariabel = [
        (1,1), (2,2), (3,3), (4,4)
    ]

    # pertanyaan
    pilihanindikator = [
        (1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7), (8,8)
    ]
    pilihanskorlikert = [
        (1,1), (2,2), (3,3), (4,4), (5,5)
    ]
    guru = models.ForeignKey(
        Teacher,
        related_name='evalguru_guru',
        on_delete=models.CASCADE)
    matapelajaran = models.ForeignKey(
        MataPelajaran,
        related_name='evalguru_matapelajaran',
        on_delete=models.CASCADE)
    siswa = models.ForeignKey(
        Student,
        related_name='evalguru_siswa',
        on_delete=models.CASCADE)
    variabel = models.PositiveIntegerField(choices=pilihanvariabel)
    indikator = models.PositiveIntegerField(choices=pilihanindikator)
    skorlikert = models.PositiveIntegerField(choices=pilihanskorlikert)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    kritik_saran = models.TextField(blank=True, null=True)