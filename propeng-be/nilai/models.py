# nilai/models.py

from django.db import models
# Pastikan path import benar
from user.models import User

class Nilai(models.Model):
    # Foreign Key ke User (Siswa)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nilai_komponen' # Nama relasi dari User ke Nilai
    )
    # Foreign Key ke Komponen Penilaian (Gunakan String Reference)
    komponen = models.ForeignKey(
        'komponenpenilaian.KomponenPenilaian', # String Reference
        on_delete=models.CASCADE, 
        related_name='nilai_siswa',
        null=True,  
        blank=True
    )
    # Field Nilai (bolehin null)
    nilai = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True 
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Pastikan hanya ada satu nilai per siswa per komponen
        unique_together = ('student', 'komponen')
        ordering = ['student', 'komponen']

    def __str__(self):
        score_display = str(self.nilai) if self.nilai is not None else "Kosong"
        # Coba akses nama komponen/matpel dengan aman
        try:
            nama_komponen = self.komponen.namaKomponen
            nama_matpel = self.komponen.mataPelajaran.nama
        except AttributeError: # Handle jika komponen atau matapelajaran None/error
            nama_komponen = f"Komponen ID {self.komponen_id}"
            nama_matpel = "N/A"
        return f"{self.student.username} - {nama_komponen} ({nama_matpel}): {score_display}"