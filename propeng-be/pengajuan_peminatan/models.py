from django.db import models
from django.utils import timezone
from matapelajaran.models import *
from tahunajaran.models import *

class Event(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)
    angkatan = models.ForeignKey(Angkatan, on_delete=models.CASCADE, null=True, blank=True, related_name="angkatan_kelas_11")

    # list matpel yg admin taro sebagai pilihan per tier
    tier1_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t1o1", null=True)
    t1o1_capacity = models.IntegerField()


    tier1_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t1o2",null=True)
    t1o2_capacity = models.IntegerField()


    tier2_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t2o1",null=True)
    t2o1_capacity = models.IntegerField()


    tier2_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t2o2",null=True)
    t2o2_capacity = models.IntegerField()
    

    tier3_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t3o1",null=True)
    t3o1_capacity = models.IntegerField()
   
    tier3_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t3o2",null=True)
    t3o2_capacity = models.IntegerField()
    
    
    tier4_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t4o1",null=True)
    t4o1_capacity = models.IntegerField()
    
    tier4_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t4o2",null=True)
    t4o2_capacity = models.IntegerField()

class PilihanSiswa(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="Linimasa")
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="siswa_memilih"
    )
    # misal kalo tier 1 dia false --> milih tier 1 option 1, kalo true tier 1 option 2 etc,
    # ringan ga menuhin memori
    tier1 = models.BooleanField(null=True, blank=True)

    # guru misal ngeliat tier 1 dia milih yg option 1 (False),
    # maka ketika reject --> choose the True (Option 2)  
    tier2 = models.BooleanField(null=True, blank=True)
    tier3 = models.BooleanField(null=True, blank=True)
    tier4 = models.BooleanField(null=True, blank=True)

    # status, false as being Rejected, True as being accepted
    statustier1 = models.BooleanField(null=True, blank=True)
    statustier2 = models.BooleanField(null=True, blank=True)
    statustier3 = models.BooleanField(null=True, blank=True)
    statustier4 = models.BooleanField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now=True)

    note = models.TextField(null=True, blank=True)



