from django.db import models
from matapelajaran.models import MataPelajaran
from user.models import User

class Nilai(models.Model):
    JENIS_NILAI_CHOICES = [
        ('UH', 'Ulangan Harian'),
        ('UTS', 'Ujian Tengah Semester'),
        ('UAS', 'Ujian Akhir Semester'),
        ('TUGAS', 'Tugas'),
    ]
    
    matapelajaran = models.ForeignKey(MataPelajaran, on_delete=models.CASCADE, related_name='nilai_siswa')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nilai_siswa')
    jenis_nilai = models.CharField(max_length=10, choices=JENIS_NILAI_CHOICES)
    nilai = models.DecimalField(max_digits=5, decimal_places=2)
    keterangan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('matapelajaran', 'student', 'jenis_nilai')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.matapelajaran.nama} - {self.get_jenis_nilai_display()} - {self.nilai}"
