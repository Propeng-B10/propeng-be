from django.db import models
from django.utils import timezone
from datetime import date
from user.models import Student
import string
import random

class AbsensiHarian(models.Model):
    kode = models.CharField('kel',null=True, unique=True, max_length=6)
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
        if len(self.listSiswa) == 0:
            studentDiKelas = self.kelas.siswa.all()
            self.listSiswa = {int(students.user_id): "Alfa" for students in studentDiKelas}
        super().save(*args, **kwargs)
    
    def update_absen(self, tipe_absensi, id_siswa):
        self.listSiswa[id_siswa] = tipe_absensi
        print(self.kode)
        print(id_siswa)
        print(tipe_absensi)
        print(self.listSiswa)
        self.save()
        if self.listSiswa[id_siswa] == tipe_absensi:
            return "Berhasil"
        else:
            return "Gagal"
    
    def check_absensi(self, id_siswa):
        print("here it is")
        print(self.listSiswa)
        print(self.listSiswa[str(id_siswa)])
        return self.listSiswa[str(id_siswa)]