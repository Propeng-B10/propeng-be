# user/apps.py (Add new signal handler)

# Standard imports for AppConfig and signals are okay at the top
import calendar # Needed in the new handler
from django.apps import AppConfig, apps # Import apps here
from django.db.models.signals import post_migrate
from django.utils import timezone
from datetime import date # Needed in handlers

# Import the attendance population utility function
# This import is okay at the top
from absensi.utils import populate_dummy_attendance_for_class


# --- YOUR ORIGINAL SIGNAL HANDLER (KEPT AS IS) ---
# Paste the ENTIRE original function code you provided here.
# Do not add or remove anything from THIS function's logic or imports.
# This function is responsible for creating Admin, Teachers, Students, Matpel, Kelas ABIL, etc.
# Its behavior, including the early 'return', is preserved.

# START OF YOUR ORIGINAL ensure_admin_exists_and_populate_data function code:
def ensure_admin_exists_and_populate_data(sender, **kwargs):
    # --- YOUR ORIGINAL TOP-LEVEL IMPORTS ARE HERE ---
    # These imports might cause AppRegistryNotReady errors during startup/migrations.
    # As per your constraint, they are left here.
    from django.contrib.auth.hashers import make_password
    from user.models import User, Teacher, Student
    from tahunajaran.models import TahunAjaran, Angkatan
    # Missing imports from your provided code:
    # from kelas.models import Kelas
    # from matapelajaran.models import MataPelajaran

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
        User.objects.filter(username="adminnext").delete()
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
        return # <--- YOUR ORIGINAL RETURN

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

    kelas_data["waliKelas"].homeroomId_id = kelas.id # Use .id
    kelas_data["waliKelas"].save()
    
    # Add students to class
    for student in students:
        kelas.siswa.add(student)
        student.isAssignedtoClass = True
        student.save()
    
    
    print(f'Created kelas: {kelas.namaKelas}')
    print('Database population completed!')
    
    kelas.generate_kode() # WARNING: This creates AbsensiHarian for today every time this block runs
    print('Kelas sudah ditambahkan satu instance Absensi Harian!')
    # END OF YOUR ORIGINAL ensure_admin_exists_and_populate_data


# --- NEW SIGNAL HANDLER FOR ATTENDANCE POPULATION (Imports Moved Inside) ---
def populate_dummy_attendance_signal_handler(sender, **kwargs):
     """
     Signal handler to populate dummy attendance data.
     This runs *in addition* to other post_migrate handlers.
     Includes a check to ensure the necessary core data (Kelas ABIL) exists first.
     """
     print("\n--- Running Attendance Population Signal Handler ---")
     try:
         # --- IMPORTS MOVED INSIDE THIS FUNCTION ---
         # Use apps.get_model() for safety within signal handlers
         from user.models import User # Get from apps registry
         from kelas.models import Kelas # Get from apps registry
         from django.utils import timezone
         from datetime import date
         import traceback # Import traceback here
         # --- END IMPORTS ---

         # Check if the critical core data (specifically the class) exists before attempting population
         # Use filter().first() to avoid DoesNotExist exception if the class isn't found
         # Using apps.get_model is correct
         Kelas_model = apps.get_model('kelas', 'Kelas')
         kelas_abil = Kelas_model.objects.filter(namaKelas='Kelas ABIL').first()

         if not kelas_abil:
             print("Kelas 'Kelas ABIL' not found by attendance signal handler. Skipping attendance population.")
             return # Do not proceed if the data we depend on isn't there

         print("Core data (Kelas ABIL) confirmed to exist. Proceeding with attendance population...")

         # Define the desired date range here
         year = timezone.now().year
         start_date_attendance = date(year, 1, 1)
         end_date_attendance = date(year, 6, 30) # Populate up to June 30th

         # Call the utility function
         if start_date_attendance <= end_date_attendance:
             populate_dummy_attendance_for_class(
                  class_name='Kelas ABIL', # Use the exact class name
                  start_date=start_date_attendance,
                  end_date=end_date_attendance
             )
             print("--- Attendance Population Signal Handler Finished ---")
         else:
             print(f"Warning: Attendance date range is invalid ({start_date_attendance} to {end_date_attendance}). Skipping population.")
             print("--- Attendance Population Signal Handler Skipped (Invalid Date Range) ---")


     except Exception as e:
         print(f"An error occurred within the Attendance Population Signal Handler: {e}")
         import traceback
         traceback.print_exc()
         print("--- Attendance Population Signal Handler Failed ---")


# --- Corrected Deployment Info Handler (Imports Moved Inside, Robust get_or_create) ---
def create_deployment_info(sender, **kwargs):
    # --- IMPORTS MOVED INSIDE THIS FUNCTION ---
    # Use apps.get_model() for safety within signal handlers
    try:
        DeploymentInfo = apps.get_model('user', 'DeploymentInfo')
    except LookupError:
         print("Warning: DeploymentInfo model not ready for creation.")
         return
    import traceback # Import traceback here if needed
    # --- END IMPORTS ---


    # Use get_or_create for idempotency to avoid creating multiple instances
    # Add a try/except around the get_or_create to handle existing duplicates gracefully
    try:
        # Check if any DeploymentInfo object exists to decide whether to create or skip
        # This is more robust than get_or_create when multiple already exist.
        if not DeploymentInfo.objects.exists():
             DeploymentInfo.objects.create()
             print("✅ DeploymentInfo instance created!")
        else:
             # You could potentially log a warning if more than one exists here
             print("✅ DeploymentInfo instance found (not created - one or more already exist).")

    except Exception as e:
         print(f"An error occurred within create_deployment_info: {e}")
         import traceback
         traceback.print_exc()


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'

    def ready(self):
        # Connect signal handlers to the post_migrate signal for THIS app (sender=self)
        # Order of connection usually determines execution order, but it's not guaranteed.
        post_migrate.connect(ensure_admin_exists_and_populate_data, sender=self)
        # Connect the NEW attendance population handler *after* the core data creator
        post_migrate.connect(populate_dummy_attendance_signal_handler, sender=self)
        # Connect deployment info handler
        post_migrate.connect(create_deployment_info, sender=self)

