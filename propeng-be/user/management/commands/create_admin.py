from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user.models import *
from tahunajaran.models import *
from kelas.models import *
from mata_pelajaran.models import *
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Creates a superuser account with predefined credentials'

    def handle(self, *args, **options):
        username = 'adminNext'
        email = 'admin@example.com'
        password = 'testpass1234'

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
                return

            # Create superuser
            admin = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin'  # Make sure the user has admin role
            )

            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"'))
            self.stdout.write(self.style.SUCCESS('Username: adminNext'))
            self.stdout.write(self.style.SUCCESS('Password: testpass1234'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Create or get Angkatan objects
        angkatan_2022, _ = Angkatan.objects.get_or_create(angkatan=2022)
        angkatan_2023, _ = Angkatan.objects.get_or_create(angkatan=2023)
        
        # Create or get TahunAjaran objects
        tahun_2024, _ = TahunAjaran.objects.get_or_create(tahunAjaran=2024)
        tahun_2025, _ = TahunAjaran.objects.get_or_create(tahunAjaran=2025)
        
        # Create Teachers
        teacher_data = [
            {
                "username": "abil.teacher",
                "password": make_password("testpass1234"),
                "role": "teacher",
                "name": "Masabil teacher",
                "nisp": "123",
            },
            {
                "username": "misyele.teacher",
                "password": make_password("testpass1234"),
                "role": "teacher",
                "name": "Michelle teacher",
                "nisp": "1234",
            }
        ]
        
        teachers = []
        for data in teacher_data:
            if not User.objects.filter(username=data["username"]).exists():
                # Create user
                user = User.objects.create(
                    username=data["username"],
                    password=data["password"],
                    role=data["role"],
                    email=f"{data['username']}@example.com"
                )
                
                # Create teacher profile
                teacher = Teacher.objects.create(
                    user=user,
                    name=data["name"],
                    nisp=data["nisp"],
                    username=data["username"]
                )
                teachers.append(teacher)
                self.stdout.write(self.style.SUCCESS(f'Created teacher: {data["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Teacher {data["username"]} already exists'))
                teacher = Teacher.objects.get(user__username=data["username"])
                teachers.append(teacher)
        
        # Create Students
        student_data = [
            {
                "username": "arshad.student",
                "password": make_password("testpass1234"),
                "role": "student",
                "name": "Arshad Student",
                "nisn": "1234",
                "angkatan": angkatan_2023
            },
            {
                "username": "ica.student",
                "password": make_password("testpass1234"),
                "role": "student",
                "name": "Icha Student",
                "nisn": "12345",
                "angkatan": angkatan_2023
            }
        ]
        
        students = []
        for data in student_data:
            if not User.objects.filter(username=data["username"]).exists():
                # Create user
                user = User.objects.create(
                    username=data["username"],
                    password=data["password"],
                    role=data["role"],
                    email=f"{data['username']}@example.com"
                )
                
                # Create student profile
                student = Student.objects.create(
                    user=user,
                    name=data["name"],
                    nisn=data["nisn"],
                    username=data["username"],
                    angkatan=data["angkatan"]
                )
                students.append(student)
                self.stdout.write(self.style.SUCCESS(f'Created student: {data["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Student {data["username"]} already exists'))
                student = Student.objects.get(user__username=data["username"])
                students.append(student)
        
        # Create Admin
        admin_data = {
            "username": "dien.admin",
            "password": make_password("testpass1234"),
            "role": "admin",
            "is_staff": True
        }
        
        if not User.objects.filter(username=admin_data["username"]).exists():
            User.objects.create(
                username=admin_data["username"],
                password=admin_data["password"],
                role=admin_data["role"],
                email=f"{admin_data['username']}@example.com",
                is_staff=admin_data["is_staff"]
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin: {admin_data["username"]}'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin {admin_data["username"]} already exists'))
        
        # Create MataPelajaran
        matpel_data = [
            {
                "kategoriMatpel": "FISIKA",
                "nama": "FISIKA KELAS 12",
                "tahunAjaran": tahun_2025,
                "angkatan": angkatan_2023,
                "teacher": teachers[0] if teachers else None
            },
            {
                "kategoriMatpel": "BIOLOGI",
                "nama": "BIOLOGI KELAS 11",
                "tahunAjaran": tahun_2025,
                "angkatan": angkatan_2023,
                "teacher": teachers[1] if len(teachers) > 1 else None
            },
            {
                "kategoriMatpel": "KIMIA",
                "nama": "KIMIA KELAS 10",
                "tahunAjaran": tahun_2025,
                "angkatan": angkatan_2023,
                "teacher": teachers[0] if teachers else None
            }
        ]
        
        for data in matpel_data:
            if data["teacher"] is None:
                self.stdout.write(self.style.WARNING(f'Skipping matpel {data["nama"]} due to missing teacher'))
                continue
                
            # Check if subject already exists
            if not MataPelajaran.objects.filter(nama=data["nama"]).exists():
                matpel = MataPelajaran.objects.create(
                    kategoriMatpel=data["kategoriMatpel"],
                    nama=data["nama"],
                    tahunAjaran=data["tahunAjaran"],
                    angkatan=data["angkatan"],
                    teacher=data["teacher"]
                )
                self.stdout.write(self.style.SUCCESS(f'Created matpel: {data["nama"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Matpel {data["nama"]} already exists'))
        
        # Create Kelas
        kelas_data = {
            "namaKelas": "Kelas ABIL",
            "tahunAjaran": tahun_2024,
            "waliKelas": teachers[0] if teachers else None,
            "angkatan": angkatan_2022
        }
        
        if kelas_data["waliKelas"] is None:
            self.stdout.write(self.style.WARNING(f'Skipping kelas {kelas_data["namaKelas"]} due to missing teacher'))
        else:
            # Check if class already exists
            if not Kelas.objects.filter(namaKelas=kelas_data["namaKelas"]).exists():
                kelas = Kelas.objects.create(
                    namaKelas=kelas_data["namaKelas"],
                    tahunAjaran=kelas_data["tahunAjaran"],
                    waliKelas=kelas_data["waliKelas"],
                    angkatan=kelas_data["angkatan"]
                )
                
                # Add students to class
                for student in students:
                    kelas.siswa.add(student)
                
                self.stdout.write(self.style.SUCCESS(f'Created kelas: {kelas_data["namaKelas"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Kelas {kelas_data["namaKelas"]} already exists'))
            
        self.stdout.write(self.style.SUCCESS('Database population completed!'))
        
    