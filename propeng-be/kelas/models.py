import random
import string
from django.db import models
from user.models import Teacher as Teacher
from user.models import Student as Student
from tahunajaran.models import TahunAjaran
from django.utils import timezone
from datetime import date, timedelta
from absensi.models import AbsensiHarian

class Kelas(models.Model):
    namaKelas = models.CharField(max_length=100)    
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.SET_NULL, null=True, blank=True)           
    isActive = models.BooleanField(default=True)  
    isDeleted = models.BooleanField(default=False)          
    angkatan = models.IntegerField(null=False, blank=False, default=2023)
    kode = models.CharField(null=True, unique=True, max_length=6, blank=True)
    kode_expiry_time = models.DateTimeField(null=True, blank=True)
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

    def generate_kode(self):
        """Generate a new kode absen and create or fetch today's AbsensiHarian."""
        today = timezone.now().date()

        # Check if there's an existing AbsensiHarian for today
        absensi_harian, created = AbsensiHarian.objects.get_or_create(
            date=today, kelas=self
        )

        # Generate a unique random 6-character code
        while True:
            kode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Kelas.objects.filter(kode=kode).exists():
                break

        # Update the kode and expiry time
        self.kode = kode
        absensi_harian.kode = kode
        absensi_harian.save()
        self.kode_expiry_time = timezone.now() + timedelta(minutes=5)
        self.save()

        return self.kode
    
    def kode_is_expired(self):
        """Check if the kode absen has expired."""
        return self.kode_expiry_time and timezone.now() > self.kode_expiry_time

    def check_kode(self, kode_absen):
        print(self.kode)
        print(kode_absen)
        if self.kode != kode_absen:
            return "Gagal"
        return "Berhasil"