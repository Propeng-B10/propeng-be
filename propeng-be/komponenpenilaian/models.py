from django.utils import timezone
from django.db import models
from matapelajaran.models import MataPelajaran # Pastikan import ini benar

# Pindahkan konstanta TIPE_NILAI ke sini jika ingin digunakan di KomponenPenilaian
PENGETAHUAN = 'Pengetahuan'
KETERAMPILAN = 'Keterampilan'
TIPE_KOMPONEN_CHOICES = [
    (PENGETAHUAN, 'Pengetahuan'),
    (KETERAMPILAN, 'Keterampilan'),
]

class KomponenPenilaian(models.Model):
    namaKomponen = models.CharField(max_length=100, blank=False, null=False)
    bobotKomponen = models.IntegerField(blank=False, null=False) # Pertimbangkan DecimalField jika perlu bobot non-integer
    tipeKomponen = models.CharField(
        max_length=15,
        choices=TIPE_KOMPONEN_CHOICES, # Gunakan choices di sini
        blank=False,
        null=False
    )
    createdAt = models.DateTimeField(default=timezone.now)

    mataPelajaran = models.ForeignKey(
        MataPelajaran,
        on_delete=models.CASCADE, # CASCADE mungkin lebih cocok, jika matpel dihapus, komponennya ikut hilang
        null=False, # Seharusnya komponen selalu terkait matpel
        related_name="komponenpenilaian_matpel"
    )

    # nilai = models.ForeignKey(
    #     "nilai.Nilai",
    #     on_delete=models.PROTECT,
    #     null=True,
    #     related_name="komponenpenilaian_nilai"
    # )

    def save(self, *args, **kwargs):
        # Tambahkan validasi atau logika lain jika perlu
        super().save(*args, **kwargs)

    def __str__(self):
        # Sertakan tipe dalam representasi string
        return f"{self.namaKomponen} ({self.get_tipeKomponen_display()}) - Bobot {self.bobotKomponen}%"

    class Meta:
        # Pastikan unik berdasarkan nama, matpel, DAN tipe
        unique_together = ('namaKomponen', 'mataPelajaran', 'tipeKomponen')
        ordering = ['mataPelajaran', 'tipeKomponen', 'namaKomponen'] # Urutan yang lebih logis