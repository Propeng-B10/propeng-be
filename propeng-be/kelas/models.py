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
    kode = models.CharField(null=True, unique=True, max_length=8, blank=True)
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

        # Jika siswa berada di kelas (dalam arti lain siswa.isAssignedtoClass = true) yang tidak aktif dan isdeleted = false, maka set isAssignedtoClass = false
        for siswa in self.siswa.all():
            if not self.isActive and not self.isDeleted:
                siswa.isAssignedtoClass = False
                siswa.save()
        super().save(*args, **kwargs)

    def generate_kode(self):
        """Generate a new 8-digit alphanumeric kode absen and create or fetch today's AbsensiHarian."""
        today = timezone.now().date()

        # 1. Ambil atau buat record AbsensiHarian untuk hari ini & kelas ini
        absensi_harian, created = AbsensiHarian.objects.get_or_create(
            date=today, kelas=self
        )

        # 2. Generate kode unik 8 karakter (MODIFIKASI DI SINI)
        while True:
            # Menggunakan huruf besar (A-Z) dan angka (0-9), panjang 8 karakter
            kode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Cek keunikan terhadap field 'kode' di model Kelas
            if not Kelas.objects.filter(kode=kode).exists():
                break

        # 3. Set kode di model Kelas dan AbsensiHarian
        self.kode = kode
        absensi_harian.kode = kode
        absensi_harian.save() # Simpan AbsensiHarian

        # 4. Set waktu kedaluwarsa (tetap 30 detik sesuai konteks sebelumnya)
        self.kode_expiry_time = timezone.now() + timedelta(seconds=30)
        ## Set refresh celery after 30s
        
        # 5. Simpan kode di model Kelas
        self.save() # Simpan Kelas (dengan kode baru & expiry time)

        return self.kode # Kembalikan kode yang baru dibuat
    def kode_is_expired(self):
        """Check if the kode absen has expired."""
        return self.kode_expiry_time and timezone.now() > self.kode_expiry_time

    def check_kode(self, kode_absen):
        
        print(self.kode)
        print("disisni")
        print(kode_absen)
        if self.kode_is_expired():
            return "Gagal"
        # Cek apakah kode yang dimasukkan sama dengan kode yang ada di kelas
        if self.kode != kode_absen:
            return "Gagal"
        return "Berhasil"