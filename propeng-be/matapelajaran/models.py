from django.db import models
from user.models import Teacher, Student
from kelas.models import TahunAjaran

class MataPelajaran(models.Model):  # Renamed from User to MataPelajaran
    MATKUL_CHOICES = [
        ("BING_WAJIB", "Bahasa Inggris Wajib"),
        ("BING_PEMINATAN", "Bahasa Inggris Peminatan"),
        ("MTK_WAJIB", "Matematika Wajib"),
        ("MTK_PEMINATAN", "Matematika Peminatan"),
        ("FISIKA", "Fisika"),
        ("KIMIA", "Kimia"),
        ("BIOLOGI", "Biologi"),
    ]

    namaMatpel = models.CharField(max_length=100, choices=MATKUL_CHOICES)
    kode = models.CharField(max_length=20, unique=True, blank=True)
    kelas = models.IntegerField()
    tahun_ajaran = models.ForeignKey(TahunAjaran,on_delete=models.SET_NULL)  # Ensure integer type for better handling

    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True,  # Fixed issue (must allow null)
        related_name="matapelajaran_diajarkan"  # Avoid reverse query conflict
    )

    siswa_terdaftar = models.ManyToManyField(
        Student, 
        blank=True, 
        related_name="matapelajaran_diikuti"  # Avoid reverse query conflict
    )

    is_archived = models.BooleanField(default=False)  # Use a better name for expiry

    class Meta:
        unique_together = ('namaMatpel', 'kelas', 'tahun_ajaran') 

    def save(self, *args, **kwargs):
        if not self.kode:  # Auto-generate kode if not provided
            self.kode = f"{self.namaMatpel.replace('_', '').upper()}_{self.kelas}_{self.tahun_ajaran}"
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
        return f"{self.get_namaMatpel_display()} ({self.kode}) - Tahun {self.tahun_ajaran}"
