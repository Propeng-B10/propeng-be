from django.db import models
from django.utils import timezone
from matapelajaran.models import *

class Event(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    # list matpel yg admin taro sebagai pilihan per tier
    tier1_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t1o1")
    tier1_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t1o2")
    tier2_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t2o1")
    tier2_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t2o2")
    tier3_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t3o1")
    tier3_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t3o2")
    tier4_option1 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t4o1")
    tier4_option2 = models.ForeignKey(MataPelajaran, on_delete=models.SET_NULL, related_name="t4o2")

class PilihanSiswa(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="Linimasa")
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="siswa_memilih"
    )
    # misal kalo tier 1 dia false --> milih tier 1 option 1, kalo true tier 1 option 2 etc,
    # ringan ga menuhin memori
    tier1 = models.BooleanField(default=None)

    # guru misal ngeliat tier 1 dia milih yg option 1 (False),
    # maka ketika reject --> choose the True (Option 2)  
    tier2 = models.BooleanField(default=None)
    tier3 = models.BooleanField(default=None)
    tier4 = models.BooleanField(default=None)
    submitted_at = models.DateTimeField(default=timezone.now)



