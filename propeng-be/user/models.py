from django.contrib.auth.models import AbstractUser
from django.db import models

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
    nisn = models.CharField(null=True, blank=True, max_length=20)
    tahun_ajaran = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - Student"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nisp = models.CharField(null=True, blank=True, max_length=20)
    homeroom_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Teacher"
