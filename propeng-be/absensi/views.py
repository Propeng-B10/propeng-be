import calendar
import traceback
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from user.views import IsTeacherRole
from .models import *
from kelas.models import *
from user.models import Student
from rest_framework.decorators import api_view, permission_classes
import re
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.utils import timezone
from datetime import datetime, date # Import datetime dan date
from rest_framework.response import Response # Gunakan Response DRF
from rest_framework import status # Gunakan status codes DRF
from collections import defaultdict # Untuk menghitung
from calendar import Calendar
from datetime import timedelta
from calendar import Calendar, monthrange

# Create your views here.

class IsStudentRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')
    
def get_month_weeks(year, month):
    """
    Returns a list of (week_start, week_end, weekdays)
    where weekdays = [Mon, Tue, Wed, Thu, Fri],
    and only those blocks with ≥3 days in month are kept—
    except in January we force week 1 to be Jan 6–10.
    """
    cal = Calendar(firstweekday=0)  # Monday first
    weeks = []

    # --- special‐case January ---
    if month == 1:
        # Force week 1 = Jan 6–10
        start = date(year, 1, 6)
        end   = date(year, 1, 10)
        weekdays = [date(year, 1, d) for d in range(6, 11)]
        weeks.append((start, end, weekdays))

        # now pick up all normal “≥3-in-month” blocks starting from the week that begins on/after Jan 13
        for block in cal.monthdatescalendar(year, month):
            mon, tue, wed, thu, fri, *rest = block
            # skip anything whose Monday is before the 13th
            if mon < date(year, 1, 13):
                continue

            wk = [mon, tue, wed, thu, fri]
            in_month = [d for d in wk if d.month == month]
            if len(in_month) >= 3:
                weeks.append((mon, fri, wk))

        return weeks

    # --- all other months: keep every Mon–Fri block with ≥3 days in the month ---
    for block in cal.monthdatescalendar(year, month):
        mon, tue, wed, thu, fri, *rest = block
        wk = [mon, tue, wed, thu, fri]
        in_month = [d for d in wk if d.month == month]
        if len(in_month) >= 3:
            weeks.append((mon, fri, wk))

    return weeks

def get_week_date_range_in_month(year, month, week_num):
    """
    Calculates the date range (Monday to Friday) for a given week number (1-based,
    relative to the first Monday of the month) of a month, clipping to the month boundaries.
    Returns (week_start_date, week_end_date).
    """
    # Get the first day of the month
    first_day_of_month = date(year, month, 1)
    # Get the last day of the month
    last_day_of_month = date(year, month, calendar.monthrange(year, month)[1])

    # Find the date of the first Monday of the month
    first_day_weekday = first_day_of_month.weekday()
    days_to_first_monday = (7 - first_day_weekday) % 7
    first_monday_of_month = first_day_of_month + timedelta(days=days_to_first_monday)

    # Calculate the Monday of the requested week number
    # Week 1's Monday is first_monday_of_month
    # Week 2's Monday is first_monday_of_month + 7 days, etc.
    week_start_date = first_monday_of_month + timedelta(days=(week_num - 1) * 7)

    # Calculate the Friday of the requested week number
    week_end_date = week_start_date + timedelta(days=4)

    # Clip the date range to the month boundaries
    clipped_week_start = max(week_start_date, first_day_of_month)
    clipped_week_end = min(week_end_date, last_day_of_month)

    # Return the clipped range
    return clipped_week_start, clipped_week_end

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_absen(request):
    absen = AbsensiHarian.objects.all()
    
    if not absen.exists():
        return JsonResponse({
            "status": 404,
            "errorMessage": "Belum ada absen yang terdaftar! Silahkan buat absen baru."
        }, status=400)

    response_data = []
    for k in absen:
        # Create a copy of the listSiswa that will include student names
        enhanced_list_siswa = {}
        
        # Iterate through each student ID in listSiswa
        for student_id, status in k.listSiswa.items():
            try:
                # Convert string ID to int if needed
                student_id_int = int(student_id)
                # Get the student object
                student = Student.objects.get(user_id=student_id_int)
                # Add to enhanced list with name
                enhanced_list_siswa[student_id] = {
                    "name": student.name,
                    "status": status["status"] if isinstance(status, dict) else status,
                    "id": student.user_id
                }
                print("perulangan ke", student_id)
                print("status", status)
            except Student.DoesNotExist:
                # If student not found, keep original status
                enhanced_list_siswa[student_id] = {
                    "name": "Unknown",
                    "status": status["status"] if isinstance(status, dict) else status,
                    "id": student_id
                }
            except Exception as e:
                # Handle any other errors
                enhanced_list_siswa[student_id] = {
                    "name": "Error",
                    "status": status["status"] if isinstance(status, dict) else status,
                    "id": student_id
                }
        
        # Add the data with enhanced student info
        response_data.append({
            "id": k.id,
            "kelas": k.kelas.namaKelas,
            "teacher": k.kelas.waliKelas.name if k.kelas.waliKelas else None,
            "absensiHari": k.date,
            "data": enhanced_list_siswa
        })

    return JsonResponse({
        "status": 201,
        "message": "Semua absen berhasil diambil!",
        "data": response_data
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentRole])
def absen(request):
    try:
        data = request.data
        id_kelas = data.get('idKelas')
        id_siswa = data.get('idSiswa')
        kode_absen = data.get('kodeAbsen')
        print(data)
        print(id_kelas)
        print(id_siswa)
        print(kode_absen)
        if not id_kelas:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada ID kelas yang dikirimkan. 'idKelas'"
            }, status=400)
        if not id_siswa:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada ID siswa yang dikirimkan. 'idSiswa'"
            }, status=400)
        if not kode_absen:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tidak ada kode absen yang dikirimkan. 'kodeAbsen'"
            }, status=400)
        print("why")
        # Get all classes to be deleted    
        kelas = Kelas.objects.get(id=id_kelas)
        student = Student.objects.get(user_id=id_siswa)
        print(kelas)
        print(student)
        if not kelas:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan."
            }, status=404)
        if not student:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan."
            }, status=404)
        print("here")
        print(timezone.now().date())
        print(AbsensiHarian.objects.filter(kelas=kelas.id, date=timezone.now().date()))
        absensi = AbsensiHarian.objects.get(kelas=kelas.id, date=timezone.now().date())
        print("this")
        if kelas.check_kode(kode_absen) == "Berhasil":
            print("tutor")
            status = absensi.update_absen("Hadir", id_siswa)
            print("jkkk")
        else:
            print("disini")
            return JsonResponse({
            "status": 400,
            "message": f"Kode yang kamu submit salah."
            }, status=200)
        if status!="Berhasil":
            return JsonResponse({
            "status": 400,
            "message": f"Terdapat permasalahan pada saat mengupdate data atas nama {student.name} untuk kelas {kelas.namaKelas}."
            }, status=200)
        return JsonResponse({
            "status": 200,
            "message": f"Siswa atas nama {student.name} berhasil absen untuk kelas {kelas.namaKelas}."
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def absensi_kelas_table(request, kelas_id):
    """
    Fetch all attendance records for a specific class and format them for a data table
    with dates as columns and students as rows
    """
    try:
        # Check if class exists
        try:
            kelas = Kelas.objects.get(id=kelas_id)
        except Kelas.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan."
            }, status=404)
            
        # Get all attendance records for this class
        absensi_records = AbsensiHarian.objects.filter(kelas=kelas).order_by('date')
        
        if not absensi_records.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Belum ada catatan absensi untuk kelas {kelas.namaKelas}."
            }, status=404)
        
        # Get all dates
        dates = [record.date.strftime('%Y-%m-%d') for record in absensi_records]
        
        # Initialize student data structure
        student_attendance = {}
        student_ids = set()
        
        # Process all attendance records to collect data
        for record in absensi_records:
            date_str = record.date.strftime('%Y-%m-%d')
            
            for student_id, data in record.listSiswa.items():
                # Handle both old and new format of listSiswa
                if isinstance(data, dict):
                    student_name = data.get("name", "Unknown")
                    status = data.get("status", "Unknown")
                    student_id_val = data.get("id", student_id)
                else:
                    # Try to get student name from database
                    try:
                        student = Student.objects.get(user_id=int(student_id))
                        student_name = student.name
                    except:
                        student_name = f"Student {student_id}"
                    status = data
                    student_id_val = student_id
                
                # Add student to tracking set
                student_ids.add(str(student_id_val))
                
                # Initialize student record if not exists
                if student_name not in student_attendance:
                    student_attendance[student_name] = {
                        "id": student_id_val,
                        "dates": {}
                    }
                
                # Add status for this date
                student_attendance[student_name]["dates"][date_str] = status
        
        # Ensure all students have entries for all dates (fill missing with "N/A")
        for student_name in student_attendance:
            for date_str in dates:
                if date_str not in student_attendance[student_name]["dates"]:
                    student_attendance[student_name]["dates"][date_str] = "N/A"
        
        return JsonResponse({
            "status": 200,
            "message": f"Data absensi untuk kelas {kelas.namaKelas} berhasil diambil!",
            "kelas": kelas.namaKelas,
            "teacher": kelas.waliKelas.name if kelas.waliKelas else None,
            "dates": dates,
            "students": student_attendance
        }, status=200)
            
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_student_absensi(request):
    """
    {
      "id": ID of the student,
      "status": Status ("Hadir", "Sakit", "Izin", or "Alfa"),
      "absensiDate": Date of the attendance record (YYYY-MM-DD)
    }
    """
    try:
        data = request.data
        student_id = data.get('id')
        status = data.get('status')
        absensi_date = data.get('absensiDate')
        if not student_id:
            return JsonResponse({
                "status": 400,
                "errorMessage": "ID Siswa diperlukan"
            }, status=400)
            
        if not status:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Status absensi diperlukan"
            }, status=400)
            
        if not absensi_date:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Tanggal absensi diperlukan"
            }, status=400)
        valid_statuses = ["Hadir", "Sakit", "Izin", "Alfa"]
        if status not in valid_statuses:
            return JsonResponse({
                "status": 400,
                "errorMessage": f"Status tidak valid. Gunakan salah satu dari: {', '.join(valid_statuses)}"
            }, status=400)
        try:
            student = Student.objects.get(user_id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Siswa dengan ID {student_id} tidak ditemukan"
            }, status=404)
            
        # Find the class the student is in
        student_classes = Kelas.objects.filter(siswa=student, isActive=True, isDeleted=False)
        if not student_classes.exists():
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Siswa dengan ID {student_id} tidak terdaftar di kelas aktif manapun"
            }, status=404)
        if not student_classes.first().isActive:
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Kelas ini sudah tidak aktif"
            }, status=404)
        try:
            if isinstance(absensi_date, str):
                from datetime import datetime
                absensi_date = datetime.strptime(absensi_date, '%Y-%m-%d').date()
                
            absensi = AbsensiHarian.objects.get(date=absensi_date, kelas=student_classes.first())
            
            student_id_str = str(student_id)
            
            if student_id_str in absensi.listSiswa:
                if isinstance(absensi.listSiswa[student_id_str], dict):
                    absensi.listSiswa[student_id_str]["status"] = status
                    absensi.listSiswa[student_id]["id"] = student_id
                else:
                    # Convert to new format
                    absensi.listSiswa[student_id_str] = {
                        "name": student.name,
                        "status": status,
                        "id": student_id
                    }
            elif student_id in absensi.listSiswa:
                if isinstance(absensi.listSiswa[student_id], dict):
                    print("works here")
                    absensi.listSiswa[student_id]["status"] = status
                    absensi.listSiswa[student_id]["id"] = student_id
                else:
                    absensi.listSiswa[student_id] = {
                        "name": student.name,
                        "status": status,
                        "id": student_id
                    }
            else:
                return JsonResponse({
                    "status": 404,
                    "errorMessage": f"Siswa dengan ID {student_id} tidak ditemukan dalam catatan absensi tanggal {absensi_date}"
                }, status=404)
                
            absensi.save()
            
            return JsonResponse({
                "status": 200,
                "message": f"Status absensi untuk {student.name} berhasil diubah menjadi {status}",
                "data": {
                    "studentId": student_id,
                    "studentName": student.name,
                    "status": status,
                    "date": absensi_date
                }
            }, status=200)
            
        except AbsensiHarian.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": f"Tidak ada catatan absensi untuk tanggal {absensi_date}"
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan: {str(e)}"
        }, status=500)

# Class permission IsStudentRole (jika belum ada, tambahkan)
class IsStudentRole(BasePermission):
    """
    Hanya mengizinkan akses untuk user dengan role 'student'.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')

# --- View Baru untuk Rekap Kehadiran Siswa ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentRole]) # Hanya siswa yang login
def get_student_attendance_summary(request):
    """
    Mengambil rekap total kehadiran (Hadir, Izin, Sakit, Alfa)
    untuk siswa yang sedang login, berdasarkan kelas aktifnya.
    Opsional: filter berdasarkan ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    try:
        user = request.user
        try:
            student_profile = Student.objects.select_related('user').get(user=user)
            if not student_profile.isActive or student_profile.isDeleted:
                 return Response({
                    "message": "Profil siswa tidak aktif.",
                    "error": True
                 }, status=status.HTTP_403_FORBIDDEN)
        except Student.DoesNotExist:
            return Response({
                "message": "Profil siswa tidak ditemukan.",
                "error": True
            }, status=status.HTTP_404_NOT_FOUND)

        # Cari Kelas Aktif Siswa
        kelas_aktif = Kelas.objects.filter(
            siswa=student_profile,
            isActive=True,
            isDeleted=False
        ).order_by('-tahunAjaran__tahunAjaran').first()

        if not kelas_aktif:
            return Response({
                "message": "Siswa tidak terdaftar di kelas aktif manapun.",
                "error": True
            }, status=status.HTTP_404_NOT_FOUND)

        # Tentukan Rentang Tanggal
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        start_date = None
        end_date = None
        date_filter_applied = False

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                date_filter_applied = True
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                date_filter_applied = True
            # Pastikan start_date tidak setelah end_date jika keduanya ada
            if start_date and end_date and start_date > end_date:
                raise ValueError("Tanggal mulai tidak boleh setelah tanggal selesai.")
        except ValueError as e:
             return Response({
                "message": f"Format tanggal tidak valid atau rentang tidak benar: {e}. Gunakan format YYYY-MM-DD.",
                "error": True
             }, status=status.HTTP_400_BAD_REQUEST)

        # Query AbsensiHarian
        absensi_query = AbsensiHarian.objects.filter(kelas=kelas_aktif).order_by('date')

        # Terapkan filter tanggal jika ada
        if start_date:
            absensi_query = absensi_query.filter(date__gte=start_date)
        if end_date:
            absensi_query = absensi_query.filter(date__lte=end_date)

        # Hitung rekap kehadiran
        # Inisialisasi counter (gunakan defaultdict agar lebih mudah)
        # Sesuaikan keys dengan status yang MUNGKIN tersimpan di listSiswa
        # Berdasarkan view update_student_absensi, sepertinya "Sakit" juga valid
        attendance_summary = defaultdict(int)
        possible_statuses = ['Hadir', 'Izin', 'Sakit', 'Alfa'] # Status yang akan dihitung

        student_id_str = str(student_profile.user_id) # Gunakan ID sebagai string key

        for record in absensi_query:
            student_data = record.listSiswa.get(student_id_str) # Coba ambil data siswa

            if student_data:
                status_siswa = None
                # Handle format lama (string) dan baru (dict)
                if isinstance(student_data, dict):
                    status_siswa = student_data.get('status')
                elif isinstance(student_data, str): # Fallback untuk format lama
                    status_siswa = student_data

                # Jika status ditemukan dan valid, increment counter
                if status_siswa in possible_statuses:
                    attendance_summary[status_siswa] += 1
                # Bisa tambahkan logika jika status tidak dikenali, misal menghitung 'Lainnya'
                # elif status_siswa:
                #    attendance_summary['Lainnya'] += 1

        # Siapkan data respons
        summary_data = {status: attendance_summary[status] for status in possible_statuses}

        response_payload = {
            "status": 200,
            "message": "Rekap kehadiran berhasil diambil.",
            "kelas_aktif": kelas_aktif.namaKelas,
            "siswa": student_profile.name or student_profile.user.username,
            "periode": {
                "start_date": start_date_str if start_date else "Awal",
                "end_date": end_date_str if end_date else "Akhir"
            },
            "rekap_kehadiran": summary_data
        }

        return Response(response_payload, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error getting student attendance summary: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            "message": "Terjadi kesalahan internal saat mengambil rekap kehadiran.",
            "error": True,
            "detail": str(e) # Optional: sertakan detail error untuk debugging
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole]) # Assuming this view is for teachers
def get_weekly_attendance_summary_details(request, kelas_id):
    """
    Get weekly attendance summary and daily details for a specific class.
    Allows specifying the week via the 'week_start' query parameter (YYYY-MM-DD).
    Defaults to the current week if 'week_start' is not provided.
    Requires the logged-in user to be the waliKelas of the class.
    """
    try:
        # 1. Get the current teacher user
        current_user = request.user
        try:
            teacher = Teacher.objects.get(user=current_user)
        except Teacher.DoesNotExist:
            return JsonResponse({
                "status": 404,
                "errorMessage": "Profil guru tidak ditemukan untuk user ini."
            }, status=404)

        # 2. Get the requested class and verify the teacher is the waliKelas
        try:
            kelas = Kelas.objects.get(id=kelas_id, waliKelas=teacher, isActive=True, isDeleted=False)
        except Kelas.DoesNotExist:
            # This covers Class not found, Class not active/deleted, OR current user is not the waliKelas
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan, tidak aktif, atau Anda bukan wali kelas untuk kelas ini."
            }, status=404)

        # 3. Determine the week start and end dates
        week_start_str = request.query_params.get('week_start')
        today = timezone.now().date()

        if week_start_str:
            try:
                # Parse the date string provided
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
                # Ensure the parsed date is actually a Monday (or adjust it to be)
                week_start = week_start - timedelta(days=week_start.weekday()) # Adjust to the Monday of that week
            except ValueError:
                return JsonResponse({
                    "status": 400,
                    "errorMessage": "Format tanggal 'week_start' tidak valid. Gunakan YYYY-MM-DD."
                }, status=400)
        else:
            # Default to the current week's Monday
            week_start = today - timedelta(days=today.weekday())

        # The week ends on Friday (weekday 4)
        week_end = week_start + timedelta(days=4)

        # 4. Get all attendance records for this class within the week (Mon-Fri)
        # __week_day lookup in Django is 1-based for Sunday, 2-based for Monday, ..., 7-based for Saturday
        weekly_attendance_records = AbsensiHarian.objects.filter(
            kelas=kelas,
            date__gte=week_start,
            date__lte=week_end,
            date__week_day__range=(2, 6) # Filter for Mon (2) to Fri (6)
        ).order_by('date')

        # 5. Get total students in the class
        total_students = kelas.siswa.count()

        # 6. Calculate Weekly Averages and prepare Daily Details
        # Initialize total counts for the entire week across all students
        weekly_total_counts = defaultdict(int)
        # Initialize possible statuses explicitly for averaging calculation
        possible_statuses = ['Hadir', 'Sakit', 'Izin', 'Alfa']
        # Ensure all possible statuses start at 0 count for the weekly total
        for status in possible_statuses:
             weekly_total_counts[status] = 0

        # Dictionary to store daily details, keyed by date string
        daily_details_dict = {}
        indonesian_days = {
            0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat"
        }

        # Initialize placeholders for all weekdays in the week, even if no record exists
        current_day_placeholder = week_start
        while current_day_placeholder <= week_end:
             if current_day_placeholder.weekday() < 5: # Only Mon-Fri
                 date_str = current_day_placeholder.strftime('%Y-%m-%d')
                 daily_details_dict[date_str] = {
                     "day_name": indonesian_days[current_day_placeholder.weekday()],
                     "date": date_str,
                     "attendance_percentage": 0.0, # Default to 0
                     "counts": {"Hadir": 0, "Sakit": 0, "Izin": 0, "Alfa": 0}, # Default counts
                     "has_record": False # Flag
                 }
             current_day_placeholder += timedelta(days=1)

        # Process each attendance record that was found for the week
        for record in weekly_attendance_records:
            date_str = record.date.strftime('%Y-%m-%d')
            day_of_week = record.date.weekday() # 0=Mon, 4=Fri

            # Ensure the record date corresponds to a weekday placeholder we created
            if date_str in daily_details_dict:
                daily_details_dict[date_str]["has_record"] = True
                daily_day_counts = defaultdict(int) # Initialize counts for THIS DAY

                # Process each student's attendance for this specific day's record
                for student_id_key, data in record.listSiswa.items():
                    # Extract status, handling both dict and string formats
                    status = data.get("status", data) if isinstance(data, dict) else data

                    # Update counts for the daily detail for THIS DAY
                    # Use status directly as the key for defaultdict
                    daily_day_counts[status] += 1

                    # Update counts for the weekly total
                    # Use status directly as the key for defaultdict
                    weekly_total_counts[status] += 1


                # After processing all students for this day's record:
                # Store daily counts and calculate daily Hadir percentage
                daily_details_dict[date_str]["counts"] = dict(daily_day_counts) # Convert back to dict

                # Calculate Hadir percentage for THIS DAY
                hadir_count_today = daily_day_counts.get("Hadir", 0)
                daily_details_dict[date_str]["attendance_percentage"] = round(
                    (hadir_count_today / total_students) * 100, 1
                )


        # Calculate weekly averages (percentages) for all statuses
        # Total number of attendance slots considered in the week (students * days with records)
        days_with_records_count = len(weekly_attendance_records)
        total_attendance_slots_processed = total_students * days_with_records_count

        weekly_averages = {}
        # Iterate through possible_statuses to ensure all are included in averages, even if 0 count
        for status in possible_statuses:
             status_total = weekly_total_counts.get(status, 0) # Get total for this status across the week
             if total_attendance_slots_processed > 0:
                  # Average is total count for status divided by total possible attendance slots
                  weekly_averages[status] = round(
                     (status_total / total_attendance_slots_processed) * 100, 1
                  )
             else:
                  weekly_averages[status] = 0.0 # Avoid division by zero

        # Prepare final daily details list, sorted by date
        daily_details_list = sorted(daily_details_dict.values(), key=lambda x: x['date'])

        # 7. Assemble the final response data
        response_data = {
            "kelas_info": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None, # Strip "Kelas " prefix
                "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                "totalSiswa": total_students
            },
            "week_info": {
                 "startDate": week_start.strftime('%Y-%m-%d'),
                 "endDate": week_end.strftime('%Y-%m-%d'),
                 # Calculate display month/week based on the week_start date
                 # Use Indonesian month names
                 "displayMonth": {
                     1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                     5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                     9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                 }.get(week_start.month, ""),
                 # Basic week number calculation: (day of month - 1) / 7 + 1
                 # This is approximate, proper week numbers require calendar logic
                 "displayWeek": f"Minggu {((week_start.day - 1) // 7) + 1}"
            },
            "weekly_averages": weekly_averages,
            "daily_details": daily_details_list # This list includes placeholders for missing days with 0s
        }

        return JsonResponse({
            "status": 200,
            "message": "Ringkasan kehadiran mingguan berhasil diambil",
            "data": response_data
        }, status=200)

    except Teacher.DoesNotExist:
        return JsonResponse({
            "status": 404,
            "errorMessage": "Profil guru tidak ditemukan."
        }, status=404)
    except Exception as e:
        # Log the error for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan internal saat mengambil ringkasan kehadiran: {str(e)}"
        }, status=500)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_monthly_student_attendance_analysis(request, kelas_id):
    """
    Get monthly attendance analysis (top/bottom students) for a specific class,
    using only the get_month_weeks(...) days as denominator.
    """
    try:
        teacher = Teacher.objects.get(user=request.user)
        kelas   = Kelas.objects.get(
            id=kelas_id, waliKelas=teacher, isActive=True, isDeleted=False
        )
        month = int(request.query_params.get('month') or 0)
        year  = int(request.query_params.get('year', timezone.now().year))
        if not 1 <= month <= 12:
            return JsonResponse({"status":400,"errorMessage":"Bulan harus 1–12"}, status=400)

        # build our week-blocks
        blocks = get_month_weeks(year, month)
        total_possible = sum(len(wk_days) for *_ , wk_days in blocks)

        # map date→record once
        start = date(year, month, 1)
        end   = date(year, month, monthrange(year, month)[1])
        records = AbsensiHarian.objects.filter(
            kelas=kelas,
            date__gte=start,
            date__lte=end
        )
        rec_by_date = {r.date: r for r in records}

        students = list(kelas.siswa.all())
        possible_statuses = ['Hadir','Sakit','Izin','Alfa']

        # initialize per-student counters
        data = {
            s.user_id: {
                "id": s.user_id,
                "name": s.name,
                "counts": dict.fromkeys(possible_statuses, 0)
            }
            for s in students
        }

        # count each status only on our block-days
        for _wstart, _wend, wk_days in blocks:
            for d in wk_days:
                rec = rec_by_date.get(d)
                if not rec:
                    continue
                for sid, st in rec.listSiswa.items():
                    sid_i = int(sid)
                    stv   = st.get("status", st) if isinstance(st, dict) else st
                    if sid_i in data and stv in possible_statuses:
                        data[sid_i]["counts"][stv] += 1

        # build analysis list
        analysis = []
        for sid, vals in data.items():
            hadir = vals["counts"]["Hadir"]
            pct   = round(hadir / total_possible * 100, 1) if total_possible else 0.0
            formatted = {s: f"{cnt} hari" for s, cnt in vals["counts"].items()}
            analysis.append({
                "id": sid,
                "name": vals["name"],
                "percentage": pct,
                "counts": formatted
            })

        # sort DESC pct, ASC name
        analysis.sort(key=lambda x: (-x["percentage"], x["name"]))

        top5    = analysis[:5]
        bottom5 = sorted(analysis, key=lambda x: (x["percentage"], x["name"]))[:5]

        return JsonResponse({
            "status":200,
            "message":"Analisis kehadiran bulanan berhasil diambil",
            "data":{
                "kelas_info":{
                    "id": kelas.id,
                    "namaKelas": re.sub(r"^Kelas\s+","",kelas.namaKelas,flags=re.IGNORECASE),
                    "waliKelas": kelas.waliKelas.name,
                    "totalSiswa": len(students)
                },
                "month_info":{
                    "year": year,
                    "monthNumber": month,
                    "monthName": calendar.month_name[month].capitalize(),
                    "startDate": start.strftime("%Y-%m-%d"),
                    "endDate":   end.strftime("%Y-%m-%d"),
                    "totalPossibleDaysInMonth": total_possible
                },
                "top_students": top5,
                "bottom_students": bottom5
            }
        }, status=200)

    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({
            "status":500,
            "errorMessage":f"Terjadi kesalahan internal saat mengambil analisis kehadiran bulanan: {e}"
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_monthly_student_attendance_detail(request, kelas_id):
    """
    Detailed monthly student attendance breakdown for a class,
    using only get_month_weeks(...) days as denominator, and sorted
    by (-percentage, name).
    """
    try:
        teacher = Teacher.objects.get(user=request.user)
        kelas   = Kelas.objects.get(
            id=kelas_id, waliKelas=teacher, isActive=True, isDeleted=False
        )
        month = int(request.query_params.get('month') or 0)
        year  = int(request.query_params.get('year', timezone.now().year))
        if not 1 <= month <= 12:
            return JsonResponse({"status":400,"errorMessage":"Bulan harus 1–12"}, status=400)

        start = date(year, month, 1)
        end   = date(year, month, monthrange(year, month)[1])
        records = AbsensiHarian.objects.filter(
            kelas=kelas,
            date__gte=start,
            date__lte=end
        )
        rec_by_date = {r.date: r for r in records}

        blocks = get_month_weeks(year, month)
        total_possible = sum(len(wk_days) for *_ , wk_days in blocks)

        students = list(kelas.siswa.all())
        possible_statuses = ['Hadir','Sakit','Izin','Alfa']
        ind_months = {
            1:"Januari",2:"Februari",3:"Maret",4:"April",
            5:"Mei",6:"Juni",7:"Juli",8:"Agustus",
            9:"September",10:"Oktober",11:"November",12:"Desember"
        }

        # accumulate per-student
        stats = {
            s.user_id: {
                "id": s.user_id,
                "name": s.name,
                "nisn": s.nisn,
                "monthly_counts": dict.fromkeys(possible_statuses, 0),
                "weekly_summary": []
            }
            for s in students
        }

        # build weekly summaries _and_ accumulate monthly_counts
        for idx, (wstart, wend, wk_days) in enumerate(blocks, start=1):
            # count each student in this block
            for s in students:
                sid = s.user_id
                cnts = dict.fromkeys(possible_statuses, 0)
                for d in wk_days:
                    rec = rec_by_date.get(d)
                    if not rec:
                        continue
                    raw = rec.listSiswa.get(str(sid))
                    if not raw:
                        continue
                    stv = raw.get("status", raw) if isinstance(raw, dict) else raw
                    if stv in possible_statuses:
                        cnts[stv] += 1
                        stats[sid]["monthly_counts"][stv] += 1

                # format the date_range
                if wstart.month == wend.month:
                    dr = f"{wstart.day} – {wend.day} {ind_months[month]}"
                else:
                    dr = f"{wstart.day} {ind_months[wstart.month]} – {wend.day} {ind_months[wend.month]}"

                stats[sid]["weekly_summary"].append({
                    "week_number": idx,
                    "date_range": f"{dr} {year}",
                    "startDate": wstart.strftime("%Y-%m-%d"),
                    "endDate":   wend.strftime("%Y-%m-%d"),
                    "counts": {st: f"{cnts[st]} hari" for st in possible_statuses},
                    "possible_days_in_week": len(wk_days)
                })

        # build final details list
        details = []
        for sid, info in stats.items():
            hadir = info["monthly_counts"]["Hadir"]
            pct   = round(hadir / total_possible * 100, 1) if total_possible else 0.0

            details.append({
                "id": sid,
                "name": info["name"],
                "nisn": info["nisn"],
                "monthly_percentage": pct,
                "monthly_counts": {
                    st: f"{info['monthly_counts'][st]} hari" for st in possible_statuses
                },
                "weekly_summary": info["weekly_summary"]
            })

        # sort by -pct, then name
        details.sort(key=lambda x: (-x["monthly_percentage"], x["name"]))

        return JsonResponse({
            "status":200,
            "message":"Detail analisis kehadiran bulanan siswa berhasil diambil",
            "data":{
                "kelas_info":{
                    "id": kelas.id,
                    "namaKelas": re.sub(r"^Kelas\s+","",kelas.namaKelas,flags=re.IGNORECASE),
                    "waliKelas": kelas.waliKelas.name,
                    "totalSiswa": len(students)
                },
                "month_info":{
                    "year": year,
                    "monthNumber": month,
                    "monthName": ind_months[month],
                    "startDate": start.strftime("%Y-%m-%d"),
                    "endDate":   end.strftime("%Y-%m-%d"),
                    "totalPossibleDaysInMonth": total_possible
                },
                "students_details": details
            }
        }, status=200)

    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({"status":500,"errorMessage":f"Internal error: {e}"},status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_yearly_attendance_summary(request, kelas_id):
    """
    Get yearly attendance summary with monthly and weekly breakdowns for a specific class.
    Only the waliKelas teacher may access.
    """
    try:
        teacher = Teacher.objects.get(user=request.user)
        kelas   = Kelas.objects.get(
            id=kelas_id,
            waliKelas=teacher,
            isActive=True,
            isDeleted=False
        )
        
        year = int(request.query_params.get('year', timezone.now().year))
        if year < 2000 or year > timezone.now().year + 5:
            raise ValueError("Tahun di luar rentang wajar.")
        
        total_students    = kelas.siswa.count()
        possible_statuses = ['Hadir', 'Sakit', 'Izin', 'Alfa']
        ind_months = {
            1:"Januari",2:"Februari",3:"Maret",4:"April",
            5:"Mei",6:"Juni",7:"Juli",8:"Agustus",
            9:"September",10:"Oktober",11:"November",12:"Desember"
        }
        cal = Calendar(firstweekday=0)  # Monday=0
        
        monthly_summaries = []
        
        for month in range(1, 13):
            # --- fetch all weekday records for that month ---
            records = AbsensiHarian.objects.filter(
                kelas=kelas,
                date__year=year,
                date__month=month,
                date__week_day__range=(2, 6)
            ).order_by('date')
            
            # --- build our calendar-week blocks & total possible days ---
            blocks = get_month_weeks(year, month)  # uses your existing helper
            total_possible_days = sum(len(wk_days) for *_ , wk_days in blocks)
            
            # --- iterate blocks exactly as before to build weekly_summaries & daily_details ---
            weeks_data    = []
            monthly_total = defaultdict(int)
            
            for idx, (wstart, wend, wk_days) in enumerate(blocks, start=1):
                # grab whatever records fall into this block
                week_recs = records.filter(date__gte=wstart, date__lte=wend)
                
                # build the same `daily_details` placeholder + fill logic
                daily = {}
                for d in wk_days:
                    date_str = d.strftime("%Y-%m-%d")
                    daily[date_str] = {
                        "day_name": ["Senin","Selasa","Rabu","Kamis","Jumat"][d.weekday()],
                        "date": date_str,
                        "counts": {s: 0 for s in possible_statuses},
                        "has_record": False,
                        "attendance_percentage": 0.0
                    }
                
                # fill in real data
                for rec in week_recs:
                    ds = rec.date.strftime("%Y-%m-%d")
                    day_counts = defaultdict(int)
                    for sid, data in rec.listSiswa.items():
                        st = data.get("status", data) if isinstance(data, dict) else data
                        if st in possible_statuses:
                            day_counts[st] += 1
                            monthly_total[st] += 1
                    hadir = min(day_counts.get("Hadir", 0), total_students)
                    pct   = round(hadir / total_students * 100, 1) if total_students else 0.0
                    daily[ds].update({
                        "has_record": True,
                        "counts": dict(day_counts),
                        "attendance_percentage": pct
                    })
                
                # first, count each status once per-day 
                weekly_tot = defaultdict(int)
                for rec in week_recs:
                    for sid, data in rec.listSiswa.items():
                        st = data.get("status", data) if isinstance(data, dict) else data
                        if st in possible_statuses:
                            weekly_tot[st] += 1

                # denominator is total_students × number of days in this week (wk_days)
                slots = total_students * len(wk_days)
                weekly_avg = {
                    s: round(weekly_tot[s] / slots * 100, 1) if slots else 0.0
                    for s in possible_statuses
                }

                # displayWeek formatting unchanged
                if wstart.month == wend.month:
                    display = f"{wstart.day} – {wend.day} {ind_months[month]}"
                else:
                    display = (
                        f"{wstart.day} {ind_months[wstart.month]} – "
                        f"{wend.day} {ind_months[wend.month]}"
                    )
                
                weeks_data.append({
                    "week_info": {
                        "startDate": wstart.strftime("%Y-%m-%d"),
                        "endDate":   wend.strftime("%Y-%m-%d"),
                        "displayWeek": f"Minggu {idx}: {display}"
                    },
                    "weekly_averages": weekly_avg,
                    "daily_details": sorted(daily.values(), key=lambda d: d["date"])
                })
            
            # --- monthly averages now use total_possible_days, not records.count() ---
            month_slots = total_students * total_possible_days
            raw_m      = {
                s: (monthly_total[s] / month_slots * 100) if month_slots else 0.0
                for s in possible_statuses
            }
            sum_m     = sum(raw_m.values())
            monthly_avg = {
                s: round((raw_m[s] / sum_m) * 100, 1) if sum_m else 0.0
                for s in possible_statuses
            }
            
            monthly_summaries.append({
                "month_info": {
                    "year": year,
                    "monthNumber": month,
                    "monthName": ind_months[month],
                    "startDate": date(year, month, 1).strftime("%Y-%m-%d"),
                    "endDate": date(year, month, monthrange(year, month)[1]).strftime("%Y-%m-%d"),
                    "totalDays": total_possible_days
                },
                "weekly_averages": {
                    st: round(week_tot[st] / slots * 100, 1) if slots else 0.0
                    for st in possible_statuses
                }
            })
        
        return JsonResponse({
            "status": 200,
            "message": "Ringkasan kehadiran tahunan berhasil diambil",
            "data": {
                "kelas_info": {
                    "id": kelas.id,
                    "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE),
                    "waliKelas": kelas.waliKelas.name,
                    "totalSiswa": total_students
                },
                "year": year,
                "monthly_summaries": monthly_summaries
            }
        }, status=200)
    
    except Teacher.DoesNotExist:
        return JsonResponse({"status":404,"errorMessage":"Profil guru tidak ditemukan."},status=404)
    except Kelas.DoesNotExist:
        return JsonResponse({"status":404,"errorMessage":"Kelas tidak ditemukan atau Anda bukan wali kelas."},status=404)
    except ValueError as ve:
        return JsonResponse({"status":400,"errorMessage":str(ve)},status=400)
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({"status":500,"errorMessage":f"Internal error: {e}"},status=500)
