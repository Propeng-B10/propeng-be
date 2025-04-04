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
    
    def update_absen(self, tipe_absensi, id_siswa):
        try:
            # Check if the ID exists and has the new format
            print("DISINI YES")
            print(self.listSiswa)
            if id_siswa in self.listSiswa and isinstance(self.listSiswa[id_siswa], dict):
                # Update the status in the dictionary
                self.listSiswa[id_siswa]["status"] = tipe_absensi
                print("ini yg jkejalan")
            # If it has the old format (just a string status)
            elif id_siswa in self.listSiswa:
                print("Disini yg kejal;an")                # Get student info
                try:
                    student = Student.objects.get(user_id=id_siswa)
                    name = student.name
                except:
                    name = "Unknown"
                
                # Convert to new format
                self.listSiswa[id_siswa] = {
                    "name": name,
                    "status": tipe_absensi,
                    "id":id_siswa
                }
            # If ID doesn't exist yet
            else:
                try:
                    student = Student.objects.get(user_id=id_siswa)
                    name = student.name
                except:
                    name = "Unknown"
                
                self.listSiswa[id_siswa] = {
                    "name": name,
                    "status": tipe_absensi,
                    "id" : id_siswa
                }
            print("udah disisni")
            print(self.listSiswa)
            
            self.save()
            print(self.date)
            print(self.listSiswa)
            # Check if update was successful
            if id_siswa in self.listSiswa and (
                (isinstance(self.listSiswa[id_siswa], dict) and self.listSiswa[id_siswa]["status"] == tipe_absensi) or
                (isinstance(self.listSiswa[id_siswa], str) and self.listSiswa[id_siswa] == tipe_absensi)
            ):
                print("berhasil kok")
                return "Berhasil"
            else:
                return "Gagal"
        except Exception as e:
            print(f"Error updating absensi: {str(e)}")
            return "Gagal"
    
    def check_absensi(self, id_siswa):
        id_siswa_str = str(id_siswa)
        print("here it is")
        print(self.listSiswa)
        
        # Handle both old and new format
        if id_siswa_str in self.listSiswa:
            if isinstance(self.listSiswa[id_siswa_str], dict):
                return self.listSiswa[id_siswa_str]["status"]
            else:
                return self.listSiswa[id_siswa_str]
        elif id_siswa in self.listSiswa:
            if isinstance(self.listSiswa[id_siswa], dict):
                return self.listSiswa[id_siswa]["status"]
            else:
                return self.listSiswa[id_siswa]
        
        return "Not found"