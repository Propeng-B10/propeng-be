from django.db import models
from user.models import Teacher as Teacher
from user.models import Student as Student
from tahunajaran.models import TahunAjaran
from django.utils import timezone
from datetime import date

class Kelas(models.Model):
    namaKelas = models.CharField(max_length=100)    
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.SET_NULL, null=True, blank=True)           
    isActive = models.BooleanField(default=True)            
    angkatan = models.IntegerField(null=False, blank=False, default=2023)
    waliKelas = models.ForeignKey(
        Teacher,
        related_name='waliKelas',
        on_delete=models.SET_NULL,
        null=True
    )
    siswa = models.ManyToManyField(
        Student,
        related_name='siswa'
    )
    createdAt = models.DateTimeField(default=timezone.now)  
    updatedAt = models.DateTimeField(auto_now=True)
    expiredAt = models.DateField(null=True, blank=True)  

    def save(self, *args, **kwargs):
        # Set expiredAt ke 1 Juli tahun setelah tahunAjaran
        if self.tahunAjaran and not self.expiredAt:
            self.expiredAt = date(self.tahunAjaran.tahunAjaran + 1, 7, 1)

        # Jika tanggal sekarang sudah melewati expiredAt, set isActive = False
        if self.expiredAt and date.today() >= self.expiredAt:
            self.isActive = False

        super().save(*args, **kwargs)