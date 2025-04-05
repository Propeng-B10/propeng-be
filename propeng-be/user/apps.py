from django.apps import AppConfig
from django.db.models.signals import post_migrate

def ensure_admin_exists_and_populate_data(sender, **kwargs):
    from django.contrib.auth.hashers import make_password
    from user.models import User, Teacher, Student
    from tahunajaran.models import TahunAjaran, Angkatan
    # Create admin user if it doesn't exist
    if not User.objects.filter(username='adminnext').exists():
        User.objects.create(
            username='adminnext',
            email='admin@example.com',
            password=make_password('testpass1234'),
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print("Admin user 'adminNext' created successfully!")
    else:
        User.objects.filter(username="adminNext").delete()
        print("Deleting user 'adminNext' created successfully!")
        User.objects.create(
            username='adminnext',
            email='admin@example.com',
            password=make_password('testpass1234'),
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print("Admin user 'adminNext' created successfully!")
    
    # Check if initial data already exists to avoid duplicating
    if User.objects.filter(username='abil.teacher').exists():
        print("Initial data already exists, skipping population.")
        return

    print("Populating database with initial data...")
    
    # Create Angkatan records
    angkatan_2023, _ = Angkatan.objects.get_or_create(angkatan=2023)
    angkatan_2022, _ = Angkatan.objects.get_or_create(angkatan=2022)
    
    # Create TahunAjaran records
    tahun_2024, created = TahunAjaran.objects.get_or_create(tahunAjaran=2024)
    tahun_2025, created = TahunAjaran.objects.get_or_create(tahunAjaran=2025)
    
    # Create Teachers
    teacher_data = [
        {
            "username": "abil.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Masabil teacher",
            "nisp": "123",
            "angkatan":angkatan_2022
        },
        {
            "username": "misyele.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Michelle teacher",
            "nisp": "1234",
            "angkatan":angkatan_2022
        },
        {
            "username": "tarreq.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Tarreq teacher",
            "nisp": "12345",
            "angkatan":angkatan_2022
        },
        {
            "username": "tedyddi.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Teddy Teacher",
            "nisp": "123456",
            "angkatan":angkatan_2022
        },
        {
            "username": "darryl.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Darryl teacher",
            "nisp": "1234567",
            "angkatan":angkatan_2022
        },
        {
            "username": "ica.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Icha teacher",
            "nisp": "12345678",
            "angkatan":angkatan_2022
        },
        {
            "username": "arshad.teacher",
            "password": make_password("testpass1234"),
            "role": "teacher",
            "name": "Arshad teacher",
            "nisp": "123456789",
            "angkatan":angkatan_2022
        }
    ]
    
    teachers = []
    for data in teacher_data:
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
            username=data["username"],
            angkatan = data["angkatan"]
        )
        teachers.append(teacher)
        print(f'Created teacher: {data["name"]}')
    
    # Create Students
    student_data = [
        {
            "username": "arshad.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Arshad Student",
            "nisn": "1234",
        },
        {
            "username": "ica.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Icha Student",
            "nisn": "12345",
        },
        {
            "username": "dien.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Dien Student",
            "nisn": "123456",
        },
        {
            "username": "darryl.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Darryl Student",
            "nisn": "1234567",
        },
        {
            "username": "tarreq.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Tarreq Student",
            "nisn": "12345678",
        },
        {
            "username": "tedyddi.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Teddy Student",
            "nisn": "123456789",
        },
        {
            "username": "misyele.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Michelle Student",
            "nisn": "1234567890",
        },
        {
            "username": "abil.student",
            "password": make_password("testpass1234"),
            "role": "student",
            "name": "Abil Student",
            "nisn": "12345678901",
        }
    ]
    
    students = []
    for data in student_data:
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
            angkatan=angkatan_2023
        )
        students.append(student)
        print(f'Created student: {data["name"]}')
    
    # Create Admin
    admin_data = {
        "username": "dien.admin",
        "password": make_password("testpass1234"),
        "role": "admin",
        "is_staff": True
    }
    
    User.objects.create(
        username=admin_data["username"],
        password=admin_data["password"],
        role=admin_data["role"],
        email=f"{admin_data['username']}@example.com",
        is_staff=admin_data["is_staff"]
    )
    print(f'Created admin: {admin_data["username"]}')
    
    # Create MataPelajaran (need to import here to avoid circular imports)
    from matapelajaran.models import MataPelajaran
    
    matpel_data = [
        {
            "kategoriMatpel": "Peminatan",
            "nama": "FISIKA KELAS 12",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[0]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "BIOLOGI KELAS 11",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[1]
        },
        {
            "kategoriMatpel": "Wajib",
            "nama": "KIMIA KELAS 10",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[0]
        },
        # 8 more MataPelajaran with kategoriMatpel "Peminatan"
        {
            "kategoriMatpel": "Peminatan",
            "nama": "MATEMATIKA MINAT",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[2]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "KIMIA MINAT",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[3]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "EKONOMI",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[4]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "GEOGRAFI",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[5]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "BAHASA INGGRIS MINAT",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[6]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "BAHASA JEPANG",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[0]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "SEJARAH MINAT",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[1]
        },
        {
            "kategoriMatpel": "Peminatan",
            "nama": "INFORMATIKA",
            "tahunAjaran": tahun_2025,
            "angkatan": angkatan_2023,
            "teacher": teachers[2]
        }
    ]
    
    for data in matpel_data:
        matpel = MataPelajaran.objects.create(
            kategoriMatpel=data["kategoriMatpel"],
            nama=data["nama"],
            tahunAjaran=data["tahunAjaran"],
            angkatan=data["angkatan"],
            teacher=data["teacher"]
        )
        print(f'Created matpel: {data["nama"]}')
    
    # Create Kelas (need to import here to avoid circular imports)
    from kelas.models import Kelas
    
    kelas_data = {
        "namaKelas": "Kelas ABIL",
        "tahunAjaran": tahun_2025,
        "waliKelas": teachers[0],
        "angkatan": angkatan_2022.angkatan
    }
    
    kelas = Kelas.objects.create(
        namaKelas=kelas_data["namaKelas"],
        tahunAjaran=kelas_data["tahunAjaran"],
        waliKelas=kelas_data["waliKelas"],
        angkatan=kelas_data["angkatan"]
    )

    kelas_data["waliKelas"].homeroomId_id = kelas
    kelas_data["waliKelas"].save()
    
    # Add students to class
    for student in students:
        kelas.siswa.add(student)
        student.isAssignedtoClass = True
        student.save()
    
    
    print(f'Created kelas: {kelas_data["namaKelas"]}')
    print('Database population completed!')
    
    kelas.generate_kode()
    print('Kelas sudah ditambahkan satu instance Absensi Harian!')


def create_deployment_info(sender, **kwargs):
    from user.models import DeploymentInfo
    DeploymentInfo.objects.create()
    print("✅ DeploymentInfo instance created!")

class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'

    def ready(self):
        post_migrate.connect(ensure_admin_exists_and_populate_data, sender=self)
        post_migrate.connect(create_deployment_info, sender=self)


