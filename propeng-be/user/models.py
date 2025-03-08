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
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.role}"
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(null=True, blank=True, max_length=32)
    username = models.CharField(null=True, blank=True, max_length=32)
    nisn = models.CharField(null=True, blank=True, max_length=20)
    tahunAjaran = models.ForeignKey(TahunAjaran, on_delete=models.CASCADE, null=False, blank=False)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Student"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(null=True, blank=True, max_length=32)
    nisp = models.CharField(null=True, blank=True, max_length=20)
    username = models.CharField(null=True, blank=True, max_length=32)
    homeroomId = models.IntegerField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Teacher"
