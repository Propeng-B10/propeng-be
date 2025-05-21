from django.utils import timezone
from django.db import models
from matapelajaran.models import MataPelajaran 

PENGETAHUAN = 'Pengetahuan'
KETERAMPILAN = 'Keterampilan'
TIPE_KOMPONEN_CHOICES = [
    (PENGETAHUAN, 'Pengetahuan'),
    (KETERAMPILAN, 'Keterampilan'),
]

class KomponenPenilaian(models.Model):
    namaKomponen = models.CharField(max_length=100, blank=False, null=False)
    bobotKomponen = models.IntegerField(blank=False, null=False) 
    tipeKomponen = models.CharField(
        max_length=15,
        choices=TIPE_KOMPONEN_CHOICES, 
        blank=False,
        null=False
    )
    createdAt = models.DateTimeField(default=timezone.now)

    mataPelajaran = models.ForeignKey(
        MataPelajaran,
        on_delete=models.CASCADE, 
        null=False, 
        related_name="komponenpenilaian_matpel"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.namaKomponen} ({self.get_tipeKomponen_display()}) - Bobot {self.bobotKomponen}%"

    class Meta:
        unique_together = ('namaKomponen', 'mataPelajaran', 'tipeKomponen')
        ordering = ['mataPelajaran', 'tipeKomponen', 'namaKomponen']