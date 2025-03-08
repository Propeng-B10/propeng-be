from django.db import models
from user.models import Teacher
from user.models import Student
from kelas.models import TahunAjaran

class Kelas(models.Model):
    namaKelas = models.CharField(max_length=100)    
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.SET_NULL)             
    isActive = models.BooleanField(default=True)            # Defaultnya aktif 
    waliKelas = models.OneToOneField(
        Teacher,
        related_name= "waliKelas",                          
        unique= True,                                       # Wali Kelas di-assign ke suatu orang aja
        on_delete= models.SET_NULL,                         # Wali Kelas jika didelete set null (soft delete)
        null= True                                
    )
    siswa = models.ManyToManyField(
        Student,
        related_name= "siswa",
    )
    createdAt = models.DateTimeField(auto_now_add=True)  
    updatedAt = models.DateTimeField(auto_now=True) 

class TahunAjaran(models.Model):
    tahunAjaran = models.IntegerField(unique=True, null=True)