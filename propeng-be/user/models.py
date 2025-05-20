from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db import models
from tahunajaran.models import TahunAjaran, Angkatan
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    email = models.EmailField(unique=False, blank=True, null=True)  # Allow blank emails
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # First save the user
        super().save(*args, **kwargs)
        
        # Then update the username in the related model
        if self.role == 'student':
            try:
                student = self.student
                if student.username != self.username:
                    student.username = self.username
                    student.save()
            except Student.DoesNotExist:
                pass
        elif self.role == 'teacher':
            try:
                teacher = self.teacher
                if teacher.username != self.username:
                    teacher.username = self.username
                    teacher.save()
            except Teacher.DoesNotExist:
                pass

    def __str__(self):
        return f"{self.username} - {self.role}"
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(null=True, blank=True, max_length=32)
    username = models.CharField(null=True, blank=True, max_length=32)
    nisn = models.CharField(null=True, blank=True, max_length=20)
    angkatan = models.ForeignKey(Angkatan, on_delete=models.CASCADE, null=True, blank=True)
    isAssignedtoClass = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Sync username with User model before saving
        if self.user:
            self.username = self.user.username


        # Set expiredAt ke 1 Juli tahun setelah tahunAjaran
        if TahunAjaran.tahunAjaran and not self.expiredAt:
            self.expiredAt = date(TahunAjaran.tahunAjaran.tahunAjaran + 1, 7, 1)

        # Jika tanggal sekarang sudah melewati expiredAt, set isActive = False
        if self.expiredAt and date.today() >= self.expiredAt:
            self.isActive = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}"
    
    

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(null=True, blank=True, max_length=32)
    nisp = models.CharField(null=True, blank=True, max_length=20)
    username = models.CharField(null=True, blank=True, max_length=32)
    homeroomId = models.ForeignKey(
        'kelas.kelas',  # Reference to the Kelas model
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='waliKelasDari'
    )
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    angkatan = models.ForeignKey(Angkatan, on_delete=models.CASCADE, null=True, blank=True)
    

    def save(self, *args, **kwargs):
        # Sync username with User model before saving
        if self.user:
            self.username = self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        if self.homeroomId is not None or self.homeroomId:
            return f"{self.user.username}"
        else:
            return f"{self.user.username}"

#cant be put in simak folder ternyata :(
class DeploymentInfo(models.Model):
    deployed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Last Deployment: {self.deployed_at}"