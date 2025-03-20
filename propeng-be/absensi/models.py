from django.db import models
from django.utils import timezone
from datetime import date
from user.models import Student
import string
import random

class AbsensiHarian(models.Model):
    kode = models.CharField(null=False, unique=True, max_length=6)
    date = models.DateField()
    kelas = models.ForeignKey('kelas.Kelas', related_name="absen_kelas", on_delete=models.CASCADE)
    listSiswa = models.JSONField(default=dict)
    TIPE_ABSENSI_CHOICES = [
       ('Hadir', 'Hadir'),
       ('Absen', 'Absen'),
       ('Izin', 'Izin'),
       ('Alfa', 'Alfa'),
   ]
    tipeAbsensi = models.CharField(max_length=100, choices=TIPE_ABSENSI_CHOICES)

    def __str__(self):
        return f"Absensi {self.kelas.namaKelas} on {self.date}"

    def save(self, *args, **kwargs):
        studentDiKelas = self.kelas.siswa.all()
        self.listSiswa = {students.user_id: "Alfa" for students in studentDiKelas}
        super().save(*args, **kwargs)
    
    def update_absen(self, tipe_absensi, id_siswa):
        siswa = Student.objects.get(user_id=id_siswa)
        self.data[siswa.user_id] = tipe_absensi
        self.save()