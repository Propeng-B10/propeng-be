from django.contrib.auth.models import AbstractUser
from django.db import models
from tahunajaran.models import TahunAjaran
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    email = models.EmailField(unique=False, blank=True, null=True)  # Allow blank emails
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.role}"
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(null=True, blank=True, max_length=32)
    username = models.CharField(null=True, blank=True, max_length=32)
    nisn = models.CharField(null=True, blank=True, max_length=20)
    angkatan = models.IntegerField(null=False, blank=False, default=2023)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(null=True, blank=True, max_length=32)
    nisp = models.CharField(null=True, blank=True, max_length=20)
    username = models.CharField(null=True, blank=True, max_length=32)
    homeroomId = models.IntegerField(null=True, blank=True)
    angkatan = models.IntegerField(null=False, blank=False, default=2023)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"
