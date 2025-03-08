from django.db import models
from user.models import Teacher
from user.models import Student
from tahunajaran.models import TahunAjaran
from django.utils import timezone

class Kelas(models.Model):
    namaKelas = models.CharField(max_length=100)    
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.SET_NULL, null=True, blank=True)           
    isActive = models.BooleanField(default=True)            # Defaultnya aktif 
    waliKelas = models.ForeignKey(
        Teacher,
        related_name= "waliKelas",                          
        on_delete= models.SET_NULL,                         # Wali Kelas jika didelete set null (soft delete)
        null= True                                
    )
    siswa = models.ManyToManyField(
        Student,
        related_name= "siswa",
    )
    createdAt = models.DateTimeField(default=timezone.now)  
    updatedAt = models.DateTimeField(auto_now=True) 
