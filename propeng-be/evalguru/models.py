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

class isianEvalGuru(models.Model):
    id = models.AutoField(primary_key=True)
    guru = models.ForeignKey(
        Teacher,
        related_name='isianEvalGuru_guru',
        on_delete=models.CASCADE)
    matapelajaran = models.ForeignKey(
        MataPelajaran,
        related_name='isianEvalGuru_matapelajaran',
        on_delete=models.CASCADE)
    siswa = models.ForeignKey(
        Student,
        related_name='isianEvalGuru_siswa',
        on_delete=models.CASCADE)
    
    # ada 2 bill inside, # isian -> {"1":{"1":3,"2":4}, "2":{"1":5,"2":3, "3":4}}
    # artinya variabel 1 indikator 1 diberi nilai 3 oleh siswa, variabel 1 indikator 2 dinilai 4, variabel 2 indikator 1 dinilai 5 dst.
    isian = models.JSONField(default=dict)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    kritik_saran = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if len(self.isian) == 0:
                data_isian = {}
                # variabel 1
                # indikator 1,2    
                data_isian["1"] = {"1": 0, "2": 0}

                # variabel 2
                # indikator 1,2,...8
                data_isian["2"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}

                # variabel 3
                # indikator 1,2
                data_isian["3"] = {"1": 0, "2": 0}

                # variabel 4
                # indikator 1,2,3
                data_isian["4"] = {"1": 0, "2": 0, "3": 0}
                self.isian = data_isian
        super().save(*args, **kwargs)