from django.db import models
from user.models import Teacher, Student
from tahunajaran.models import TahunAjaran, Angkatan
import uuid

class MataPelajaran(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Add UUID field
    MATKUL_CHOICES = [
        ("BING_WAJIB", "Bahasa Inggris Wajib"),
        ("BING_PEMINATAN", "Bahasa Inggris Peminatan"),
        ("MTK_WAJIB", "Matematika Wajib"),
        ("MTK_PEMINATAN", "Matematika Peminatan"),
        ("FISIKA", "Fisika"),
        ("KIMIA", "Kimia"),
        ("BIOLOGI", "Biologi"),
    ]

    nama = models.TextField(max_length=100)
    kategoriMatpel = models.CharField(max_length=50, choices=MATKUL_CHOICES)
    kode = models.CharField(max_length=20, unique=False, blank=True)
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.SET_NULL, null=True, blank=True)
    angkatan = models.ForeignKey(Angkatan, on_delete=models.CASCADE, null=True, blank=True)
    
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

    is_archived = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.kode:  # Auto-generate kode if not provided
            self.kode = f"{self.kategoriMatpel.replace('_', '').upper()}_{self.tahunAjaran}"
        super().save(*args, **kwargs)


    def archive(self):
        """Method to archive the subject"""
        self.is_archived = True
        self.save()

    def unarchive(self):
        """Method to unarchive the subject"""
        self.is_archived = False
        self.save()

    def __str__(self):
        return f"{self.get_kategoriMatpel_display()} ({self.kode}) - Tahun {self.tahunAjaran}"
