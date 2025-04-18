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
            # Initialize dictionary to store student data
            student_data = {}
            
            # Populate the dictionary with student IDs, names, and default attendance status
            for student in studentDiKelas:
                student_data[student.user_id] = {
                    "name": student.name,
                    "status": "Alfa",
                    "id": student.user_id
                }
            
            self.listSiswa = student_data
        super().save(*args, **kwargs)
    