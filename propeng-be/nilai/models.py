from django.db import models
from matapelajaran.models import MataPelajaran
from user.models import User

class Nilai(models.Model):
    matapelajaran = models.ForeignKey(MataPelajaran, on_delete=models.CASCADE, related_name='nilai_siswa')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nilai_siswa')
    nilai = models.DecimalField(max_digits=5, decimal_places=2)
    keterangan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('matapelajaran', 'student')  # jenis_nilai dihapus dari sini
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.matapelajaran.nama} - {self.nilai}"
