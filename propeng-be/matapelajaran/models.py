from django.utils import timezone
from django.db import models
from user.models import Teacher, Student
from tahunajaran.models import TahunAjaran, Angkatan
import uuid

class MataPelajaran(models.Model):
    MATPEL_CATEGORY = [
        ("Wajib", "Wajib"), 
        ("Peminatan", "Peminatan")
    ]

    nama = models.CharField(max_length=100, default="Default Subject", blank=False, null=False)
    kategoriMatpel = models.CharField(max_length=10, choices=MATPEL_CATEGORY, default="Wajib")
    kode = models.CharField(max_length=20, unique=False, blank=True)
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.SET_NULL, null=True, blank=True)
    angkatan = models.ForeignKey(Angkatan, on_delete=models.CASCADE, null=True, blank=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)
    isDeleted = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True)
    
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="matapelajaran_diajarkan"
    )

    siswa_terdaftar = models.ManyToManyField(
        Student, 
        blank=True, 
        related_name="matapelajaran_diikuti"
    )

    def save(self, *args, **kwargs):
        if not self.kode:  # Auto-generate kode if not provided
            self.kode = f"{self.kategoriMatpel.replace('_', '').upper()}_{self.tahunAjaran}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_kategoriMatpel_display()} ({self.kode}) - Tahun {self.tahunAjaran}"
