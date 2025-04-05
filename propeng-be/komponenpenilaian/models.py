from django.utils import timezone
from django.db import models
from matapelajaran.models import MataPelajaran
from nilai.models import Nilai

class KomponenPenilaian(models.Model):
    namaKomponen = models.CharField(max_length=100, blank=False, null=False)  # <- removed unique=True
    bobotKomponen = models.IntegerField(blank=False, null=False) 
    createdAt = models.DateTimeField(default=timezone.now)

    mataPelajaran = models.ForeignKey(
        MataPelajaran,
        on_delete=models.SET_NULL,
        null=True,
        related_name="komponenpenilaian_matpel"
    )

    nilai = models.ForeignKey(
        Nilai,
        on_delete=models.PROTECT,
        null=True,
        related_name="komponenpenilaian_nilai"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.namaKomponen} - Bobot {self.bobotKomponen}%"

    class Meta:
        unique_together = ('namaKomponen', 'mataPelajaran')