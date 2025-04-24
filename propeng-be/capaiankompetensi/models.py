# capaian/models.py (Versi tanpa field 'kode')

from django.db import models
# Pastikan path impor ini sesuai dengan struktur proyek Anda
from matapelajaran.models import MataPelajaran

class CapaianKompetensi(models.Model):
    PENGETAHUAN = 'Pengetahuan'
    KETERAMPILAN = 'Keterampilan'

    TIPE_KOMPETENSI_CHOICES = [
        (PENGETAHUAN, 'Pengetahuan'),
        (KETERAMPILAN, 'Keterampilan'),
    ]

    mata_pelajaran = models.ForeignKey(
        MataPelajaran,
        on_delete=models.CASCADE,
        related_name="capaian_kompetensi"
    )
    tipe = models.CharField(
        max_length=20,
        choices=TIPE_KOMPETENSI_CHOICES,
        blank=False,
        null=False
    )
    deskripsi = models.TextField(
        blank=False,
        null=False
    )
    # Field 'kode' telah dihapus dari sini
    # kode = models.CharField(max_length=50, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('mata_pelajaran', 'tipe')
        ordering = ['mata_pelajaran', 'tipe']

    def __str__(self):
        try:
            mapel_nama = self.mata_pelajaran.nama
        except MataPelajaran.DoesNotExist:
            mapel_nama = "[Mapel Dihapus]"
        except AttributeError:
             mapel_nama = "[Mapel Belum Tersimpan]"
        return f"{mapel_nama} - {self.tipe}"