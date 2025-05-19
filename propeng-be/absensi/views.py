import calendar
from django.http import JsonResponse
from django.shortcuts import render

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

# Create your views here.

class IsStudentRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')
    
def get_week_of_month(date_obj):
    """
    Calculates the week number within the month (1-based), where Week 1 starts
    on the first Monday of the month. Days before the first Monday are not in any week of this month.
    """
    first_day_of_month = date_obj.replace(day=1)
    # Find the date of the first Monday of the month
    # weekday() returns 0 for Monday, 6 for Sunday.
    # If the 1st is a Monday, days_to_first_monday = 0
    # If the 1st is Tuesday (1), days_to_first_monday = 6 (next Monday)
    # If the 1st is Sunday (6), days_to_first_monday = 1 (next Monday)
    first_day_weekday = first_day_of_month.weekday()
    days_to_first_monday = (7 - first_day_weekday) % 7 # Days to add to 1st to get to the first Monday
    first_monday_of_month = first_day_of_month + timedelta(days=days_to_first_monday)

    # If the given date is before the first Monday of the month, it's not in a week of this month
    if date_obj < first_monday_of_month:
        return 0 # Indicates it's before Week 1

    # Number of days from the first Monday of the month to the given date
    days_from_first_monday = (date_obj - first_monday_of_month).days

    # The week number (1-based) is the number of full 7-day periods since the first Monday + 1
    week_num = (days_from_first_monday // 7) + 1
    return week_num

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
@permission_classes([IsAuthenticated, IsTeacherRole]) # Assuming only teachers can access this
def get_monthly_student_attendance_analysis(request, kelas_id):
    """
    Get monthly attendance analysis (top/bottom students) for a specific class.
    Requires 'month' (1-12) and optional 'year' query parameters.
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
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan, tidak aktif, atau Anda bukan wali kelas untuk kelas ini."
            }, status=404)

        # 3. Get and validate month and year from query parameters
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year', timezone.now().year) # Default to current year

        if not month_param:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter query 'month' (1-12) wajib disertakan."
            }, status=400)

        try:
            month = int(month_param)
            year = int(year_param)
            if not 1 <= month <= 12:
                 return JsonResponse({
                    "status": 400,
                    "errorMessage": "Parameter 'month' harus berupa angka antara 1 dan 12."
                }, status=400)
            # Ensure year is reasonable (e.g., not before 1900)
            if year < 1900 or year > timezone.now().year + 5: # Example reasonable range
                 return JsonResponse({
                    "status": 400,
                    "errorMessage": f"Parameter 'year' tidak valid. Gunakan tahun yang masuk akal (cth. 1900 - {timezone.now().year + 5})."
                }, status=400)

        except ValueError:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter 'month' dan 'year' harus berupa angka."
            }, status=400)

        # 4. Determine the date range for the month
        try:
            # Get the last day of the month
            last_day_of_month = calendar.monthrange(year, month)[1]
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day_of_month)
        except calendar.IllegalMonthError:
             return JsonResponse({
                "status": 400,
                "errorMessage": "Bulan yang diminta tidak valid."
            }, status=400)
        except ValueError as e:
             return JsonResponse({
                "status": 400,
                "errorMessage": f"Tanggal yang diminta tidak valid: {e}"
            }, status=400)


        # 5. Get all attendance records for this class within the month (Mon-Fri only count towards total days)
        # We need all records within the month, but only weekdays contribute to possible attendance days.
        all_records_in_month = AbsensiHarian.objects.filter(
            kelas=kelas,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by('date')

        # Calculate the total number of possible attendance days (number of Mon-Fri records)
        # This is the denominator for the attendance percentage.
        total_possible_days_in_month = all_records_in_month.filter(date__week_day__range=(2, 6)).count()

        # 6. Get all students in the class
        students_in_class = kelas.siswa.all()
        if not students_in_class.exists():
             # Still return 200 but indicate no students and provide empty lists
             response_data = {
                "kelas_info": {
                    "id": kelas.id,
                    "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                    "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                    "totalSiswa": 0
                },
                 "month_info": {
                    "year": year,
                    "monthNumber": month,
                    "monthName": calendar.month_name[month], # English month name
                    "startDate": start_date.strftime('%Y-%m-%d'),
                    "endDate": end_date.strftime('%Y-%m-%d'),
                    "totalPossibleDays": 0 # No students, so 0 possible days counted for students
                },
                "top_students": [],
                "bottom_students": []
             }
             return JsonResponse({
                "status": 200,
                "message": "Kelas ini tidak memiliki siswa, tidak ada data analisis.",
                "data": response_data
            }, status=200)

        # 7. Process attendance records to calculate counts per student for the month
        student_monthly_data = {}
        for student in students_in_class:
             student_monthly_data[student.user_id] = {
                 "id": student.user_id,
                 "name": student.name,
                 "counts": {"Hadir": 0, "Sakit": 0, "Izin": 0, "Alfa": 0},
                 "percentage": 0.0,
                 "total_possible_days": total_possible_days_in_month # Initialize possible days
             }

        # Iterate through all records in the month to accumulate counts for each student
        # We only need to process records for weekdays that count towards the percentage denominator.
        weekday_records_in_month = all_records_in_month.filter(date__week_day__range=(2, 6)) # Filter here again

        for record in weekday_records_in_month:
            # Iterate through the student attendance data for THIS specific day
            for student_id_key, data in record.listSiswa.items():
                try:
                    student_user_id = int(student_id_key)
                except ValueError:
                    continue # Skip if the key isn't a valid student ID

                # Check if this student is in the class we are analyzing (should be, based on how listSiswa is populated)
                # and if they were initialized in student_monthly_data
                if student_user_id in student_monthly_data:
                    # Extract status, handling both dict and string formats
                    status = data.get("status", data) if isinstance(data, dict) else data

                    # Increment the count for this status for this student
                    if status in student_monthly_data[student_user_id]["counts"]:
                        student_monthly_data[student_user_id]["counts"][status] += 1
                    # else: # Optional: Handle unexpected status if needed


        # 8. Calculate percentage for each student and prepare final student list
        student_analysis_list = []
        for student_id, data in student_monthly_data.items():
            hadir_count = data["counts"].get("Hadir", 0)
            percentage = 0.0
            if total_possible_days_in_month > 0:
                percentage = (hadir_count / total_possible_days_in_month) * 100

            # Format day counts
            formatted_counts = {
                status: f'{count} hari' for status, count in data["counts"].items()
            }


            student_analysis_list.append({
                "id": data["id"],
                "name": data["name"],
                "percentage": round(percentage, 1), # Round percentage
                "counts": formatted_counts
            })

        # 9. Sort students and get top/bottom 3
        # Sort by percentage ascending to easily get bottom (start) and top (end)
        student_analysis_list.sort(key=lambda x: x['percentage'])

        # Get bottom 3
        bottom_students = student_analysis_list[:min(3, len(student_analysis_list))] # Take up to 3

        # Sort by percentage descending for top 3
        student_analysis_list.sort(key=lambda x: x['percentage'], reverse=True)

        # Get top 3
        top_students = student_analysis_list[:min(3, len(student_analysis_list))] # Take up to 3

        # 10. Assemble the final response data
        response_data = {
            "kelas_info": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                "totalSiswa": students_in_class.count()
            },
            "month_info": {
                "year": year,
                "monthNumber": month,
                 # Use Indonesian month names for display
                 "monthName": {
                     1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                     5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                     9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                 }.get(month, ""),
                 "startDate": start_date.strftime('%Y-%m-%d'),
                 "endDate": end_date.strftime('%Y-%m-%d'),
                 "totalPossibleDaysInMonth": total_possible_days_in_month # Total weekdays with records
            },
            "top_students": top_students,
            "bottom_students": bottom_students
        }

        return JsonResponse({
            "status": 200,
            "message": "Analisis kehadiran bulanan berhasil diambil",
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
            "errorMessage": f"Terjadi kesalahan internal saat mengambil analisis kehadiran bulanan: {str(e)}"
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole]) # Assuming only teachers can access this
def get_monthly_student_attendance_detail(request, kelas_id):
    """
    Get detailed monthly student attendance breakdown for a specific class,
    including overall monthly percentage and weekly summaries.
    Requires 'month' (1-12) and optional 'year' query parameters.
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
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan, tidak aktif, atau Anda bukan wali kelas untuk kelas ini."
            }, status=404)

        # 3. Get and validate month and year from query parameters
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year', str(timezone.now().year)) # Default to current year string

        if not month_param:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter query 'month' (1-12) wajib disertakan."
            }, status=400)

        try:
            month = int(month_param)
            year = int(year_param)
            if not 1 <= month <= 12:
                 return JsonResponse({
                    "status": 400,
                    "errorMessage": "Parameter 'month' harus berupa angka antara 1 dan 12."
                }, status=400)
             # Add a basic year check, adjust range as needed
            if year < 2000 or year > timezone.now().year + 5:
                 return JsonResponse({
                    "status": 400,
                    "errorMessage": f"Parameter 'year' tidak valid. Gunakan tahun yang masuk akal (cth. 2000 - {timezone.now().year + 5})."
                }, status=400)

        except ValueError:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter 'month' dan 'year' harus berupa angka valid."
            }, status=400)

        # 4. Determine the date range for the month
        try:
            start_date_month = date(year, month, 1)
            last_day_of_month = calendar.monthrange(year, month)[1]
            end_date_month = date(year, month, last_day_of_month)
        except (calendar.IllegalMonthError, ValueError) as e:
             return JsonResponse({
                "status": 400,
                "errorMessage": f"Bulan atau tahun yang diminta tidak valid: {e}"
            }, status=400)

        # 5. Get all attendance records for this class within the monthly range (only process weekdays)
        # We only need records for weekdays within the month to count attendance.
        weekday_records_in_month_queryset = AbsensiHarian.objects.filter(
            kelas=kelas,
            date__gte=start_date_month,
            date__lte=end_date_month,
            date__week_day__range=(2, 6) # Filter for Mon (2) to Fri (6)
        ).order_by('date')

        # Calculate the total number of possible attendance days (number of Mon-Fri records found)
        # This is the denominator for the monthly attendance percentage.
        total_possible_days_in_month = weekday_records_in_month_queryset.count()

        # 6. Get all students in the class
        students_in_class = kelas.siswa.all()
        if not students_in_class.exists():
             response_data = {
                "kelas_info": {
                    "id": kelas.id,
                    "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                    "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                    "totalSiswa": 0
                },
                 "month_info": {
                    "year": year,
                    "monthNumber": month,
                    "monthName": {
                         1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                         5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                         9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                     }.get(month, ""),
                    "startDate": start_date_month.strftime('%Y-%m-%d'),
                    "endDate": end_date_month.strftime('%Y-%m-%d'),
                    "totalPossibleDaysInMonth": 0
                },
                "students_details": []
             }
             return JsonResponse({
                "status": 200,
                "message": "Kelas ini tidak memiliki siswa, tidak ada data analisis detail.",
                "data": response_data
            }, status=200)

        # 7. Aggregate attendance data per student and per week (using corrected week number)
        student_data_aggregator = {} # {student_id: {monthly_counts: {...}, weekly_counts: {week_num: {...}}}}
        possible_statuses = ['Hadir', 'Sakit', 'Izin', 'Alfa']

        # Keep track of unique week numbers encountered in the records
        unique_week_numbers_in_month_data = set()

        for student in students_in_class:
             student_data_aggregator[student.user_id] = {
                 "id": student.user_id,
                 "name": student.name,
                 "nisn": student.nisn,
                 "monthly_counts": defaultdict(int),
                 "weekly_counts": defaultdict(lambda: defaultdict(int)) # Nested defaultdict: week_num -> status -> count
             }
             # Initialize monthly counts for all statuses
             for status in possible_statuses:
                  student_data_aggregator[student.user_id]["monthly_counts"][status] = 0


        # Iterate through each attendance record for the month's weekdays
        for record in weekday_records_in_month_queryset:
             current_date = record.date

             # *** CORRECTED Week Number Calculation ***
             week_of_month = get_week_of_month(current_date)
             unique_week_numbers_in_month_data.add(week_of_month)


             # Process each student's status in this daily record
             for student_id_key, data in record.listSiswa.items():
                  try:
                       student_user_id = int(student_id_key)
                  except ValueError:
                       continue # Skip if key isn't a valid integer ID

                  # Only process if the student ID is actually in the class's student list
                  if student_user_id in student_data_aggregator:
                       # Extract status, handling both dict and string formats
                       status = data.get("status", data) if isinstance(data, dict) else data

                       # Increment monthly count
                       if status in possible_statuses:
                           student_data_aggregator[student_user_id]["monthly_counts"][status] += 1

                       # Increment weekly count for the specific week (using corrected week_of_month)
                       if status in possible_statuses:
                            student_data_aggregator[student_user_id]["weekly_counts"][week_of_month][status] += 1

        # 8. Calculate percentages and format the final student details list
        students_details_list = []
        for student_id, agg_data in student_data_aggregator.items():
            monthly_hadir_count = agg_data["monthly_counts"].get("Hadir", 0)
            monthly_percentage = 0.0
            # Use total_possible_days_in_month for the denominator if > 0
            if total_possible_days_in_month > 0:
                percentage = (monthly_hadir_count / total_possible_days_in_month) * 100


            # Prepare weekly summaries for this student
            weekly_summary_list = []
            # Use the unique week numbers found in the data, sorted
            sorted_week_nums = sorted(list(unique_week_numbers_in_month_data))

            # For each week number that had records in this month
            for week_num in sorted_week_nums:
                 week_counts = agg_data["weekly_counts"].get(week_num, defaultdict(int)) # Get counts for this week num (defaultdict(int) if no entries)

                 # *** CORRECTED Week Date Range Calculation ***
                 clipped_week_start, clipped_week_end = get_week_date_range_in_month(year, month, week_num)

                 # Determine the display date range string
                 display_date_range = f"{clipped_week_start.day} {calendar.month_abbr[clipped_week_start.month]} - {clipped_week_end.day} {calendar.month_abbr[clipped_week_end.month]} {clipped_week_end.year}".replace('.', '') # Use clipped dates and remove dots from abbr


                 # Need the number of possible attendance days *within this specific week's clipped date range*
                 # Filter the original weekday_records_in_month_queryset for the specific clipped date range of this week
                 possible_days_in_this_week = weekday_records_in_month_queryset.filter(
                     date__gte=clipped_week_start,
                     date__lte=clipped_week_end
                 ).count()


                 # Format weekly counts (ensure all statuses are included even if count is 0 for the week)
                 formatted_weekly_counts = {
                     status: f'{week_counts.get(status, 0)} hari' for status in possible_statuses
                 }

                 weekly_summary_list.append({
                     "week_number": week_num,
                     "date_range": display_date_range,
                     "startDate": clipped_week_start.strftime('%Y-%m-%d'),
                     "endDate": clipped_week_end.strftime('%Y-%m-%d'),
                     "counts": formatted_weekly_counts,
                     "possible_days_in_week": possible_days_in_this_week
                 })

            # Format monthly counts (ensure all statuses are included even if count is 0 for the month)
            formatted_monthly_counts = {
                 status: f'{agg_data["monthly_counts"].get(status, 0)} hari' for status in possible_statuses
            }


            students_details_list.append({
                "id": agg_data["id"],
                "name": agg_data["name"],
                "nisn": agg_data["nisn"],
                "monthly_percentage": round(monthly_percentage, 1),
                "monthly_counts": formatted_monthly_counts,
                "weekly_summary": weekly_summary_list
            })

        # 9. Sort students by monthly percentage (highest first)
        students_details_list.sort(key=lambda x: x['monthly_percentage'], reverse=True)

        # 10. Assemble the final response data
        response_data = {
            "kelas_info": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                "totalSiswa": students_in_class.count()
            },
            "month_info": {
                "year": year,
                "monthNumber": month,
                "monthName": {
                     1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                     5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                     9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                 }.get(month, ""),
                 "startDate": start_date_month.strftime('%Y-%m-%d'),
                 "endDate": end_date_month.strftime('%Y-%m-%d'),
                 "totalPossibleDaysInMonth": total_possible_days_in_month # Count of weekdays with records
            },
            "students_details": students_details_list
        }

        return JsonResponse({
            "status": 200,
            "message": "Detail analisis kehadiran bulanan siswa berhasil diambil",
            "data": response_data
        }, status=200)

    except Teacher.DoesNotExist:
        return JsonResponse({
            "status": 404,
            "errorMessage": "Profil guru tidak ditemukan."
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan internal saat mengambil detail analisis kehadiran bulanan: {str(e)}"
        }, status=500)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole]) # Assuming this view is for teachers
def get_monthly_class_attendance_overview(request, kelas_id):
    """
    Get monthly class attendance overview (average percentages and daily details)
    for a specific class.
    Requires 'month' (1-12) and optional 'year' query parameters.
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
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan, tidak aktif, atau Anda bukan wali kelas untuk kelas ini."
            }, status=404)

        # 3. Get and validate month and year from query parameters
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year', str(timezone.now().year)) # Default to current year string

        if not month_param:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter query 'month' (1-12) wajib disertakan."
            }, status=400)

        try:
            month = int(month_param)
            year = int(year_param)
            if not 1 <= month <= 12:
                 return JsonResponse({
                    "status": 400,
                    "errorMessage": "Parameter 'month' harus berupa angka antara 1 dan 12."
                }, status=400)
            if year < 2000 or year > timezone.now().year + 5:
                 return JsonResponse({
                    "status": 400,
                    "errorMessage": f"Parameter 'year' tidak valid. Gunakan tahun yang masuk akal (cth. 2000 - {timezone.now().year + 5})."
                }, status=400)

        except ValueError:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter 'month' dan 'year' harus berupa angka valid."
            }, status=400)

        # 4. Determine the date range for the month
        try:
            last_day_of_month = calendar.monthrange(year, month)[1]
            start_date_month = date(year, month, 1)
            end_date_month = date(year, month, last_day_of_month)
        except (calendar.IllegalMonthError, ValueError) as e:
             return JsonResponse({
                "status": 400,
                "errorMessage": f"Bulan atau tahun yang diminta tidak valid: {e}"
            }, status=400)


        # 5. Get all attendance records for this class within the monthly range (Mon-Fri only)
        # We only need records for weekdays in the month's date range
        weekday_records_in_month_queryset = AbsensiHarian.objects.filter(
            kelas=kelas,
            date__gte=start_date_month,
            date__lte=end_date_month,
            date__week_day__range=(2, 6) # Filter for Mon (2) to Fri (6)
        ).order_by('date')

        # Store records in a dictionary for quick lookup by date string
        weekday_records_dict = {record.date.strftime('%Y-%m-%d'): record for record in weekday_records_in_month_queryset}

        # Calculate the total number of possible attendance days (number of Mon-Fri records found)
        total_possible_days_in_month = weekday_records_in_month_queryset.count()


        # 6. Get total students in the class
        total_students = kelas.siswa.count()

        # If no students or no attendance records for the month, return early
        if total_students == 0 or total_possible_days_in_month == 0:
             response_data = {
                "kelas_info": {
                    "id": kelas.id,
                    "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                    "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                    "totalSiswa": total_students # Can be 0
                },
                 "month_info": {
                    "year": year,
                    "monthNumber": month,
                    "monthName": {
                         1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                         5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                         9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                     }.get(month, ""),
                    "startDate": start_date_month.strftime('%Y-%m-%d'),
                    "endDate": end_date_month.strftime('%Y-%m-%d'),
                    "totalPossibleDaysInMonth": total_possible_days_in_month # Can be 0
                },
                "monthly_averages": {"Hadir": 0.0, "Sakit": 0.0, "Izin": 0.0, "Alfa": 0.0},
                "daily_details": []
             }
             message = "Kelas ini tidak memiliki siswa" if total_students == 0 else "Tidak ada catatan absensi untuk bulan ini."
             return JsonResponse({
                "status": 200,
                "message": message,
                "data": response_data
            }, status=200)


        # 7. Calculate Monthly Averages and prepare Daily Details
        # Initialize total counts for the entire month across all students
        monthly_total_counts = defaultdict(int)
        possible_statuses = ['Hadir', 'Sakit', 'Izin', 'Alfa']
        for status in possible_statuses:
             monthly_total_counts[status] = 0


        # Dictionary to store daily details for all weekdays in the month
        daily_details_list = [] # Will store dictionaries for each day

        # Iterate through each day of the month
        current_day = start_date_month
        while current_day <= end_date_month:
            # Only process weekdays
            if current_day.weekday() < 5: # 0=Mon, ..., 4=Fri
                date_str = current_day.strftime('%Y-%m-%d')
                day_name = {
                    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat"
                }.get(current_day.weekday(), "")

                daily_day_counts = {"Hadir": 0, "Sakit": 0, "Izin": 0, "Alfa": 0}
                attendance_percentage_today = 0.0
                has_record_today = False

                # Check if there is an attendance record for this specific day
                record = weekday_records_dict.get(date_str)

                if record:
                    has_record_today = True
                    current_day_total_students = 0 # Recalculate student count for this specific record

                    # Process each student's status in this daily record
                    for student_id_key, data in record.listSiswa.items():
                        # Extract status, handling both dict and string formats
                        status = data.get("status", data) if isinstance(data, dict) else data

                        # Update counts for the daily detail for THIS DAY
                        if status in possible_statuses:
                            daily_day_counts[status] += 1

                        # Update counts for the monthly total
                        if status in possible_statuses:
                             monthly_total_counts[status] += 1

                        # Count students who have an entry in this record
                        current_day_total_students += 1


                    # Calculate Hadir percentage for THIS DAY based on students IN THIS RECORD
                    # Or, maybe better, based on total_students in the class if all students are expected to have an entry?
                    # Assuming listSiswa contains all students in the class (default behavior in save())
                    if total_students > 0:
                         attendance_percentage_today = round(
                            (daily_day_counts.get("Hadir", 0) / total_students) * 100, 1
                         )

                # Append daily detail for this day
                daily_details_list.append({
                    "day_name": day_name,
                    "date": date_str,
                    "attendance_percentage": attendance_percentage_today,
                    "counts": daily_day_counts,
                    "has_record": has_record_today
                })

            # Move to the next day
            current_day += timedelta(days=1)

        # 8. Calculate monthly averages (percentages) for all statuses
        # Total number of attendance slots considered in the month (students * days with records)
        # Use total_possible_days_in_month as the number of days that actually had records
        total_attendance_slots_processed = total_students * total_possible_days_in_month

        monthly_averages = {}
        if total_attendance_slots_processed > 0:
            # Calculate raw percentages first
            raw_percentages = {}
            total_raw_percentage = 0
            for status in possible_statuses:
                status_total = monthly_total_counts.get(status, 0)
                raw_percentage = (status_total / total_attendance_slots_processed) * 100
                raw_percentages[status] = raw_percentage
                total_raw_percentage += raw_percentage

            # Normalize percentages to ensure they sum to 100%
            if total_raw_percentage > 0:  # Avoid division by zero
                for status in possible_statuses:
                    normalized_percentage = (raw_percentages[status] / total_raw_percentage) * 100
                    monthly_averages[status] = round(normalized_percentage, 1)
            else:
                # If no attendance records, set all to 0
                for status in possible_statuses:
                    monthly_averages[status] = 0.0
        else:
            # If no records found in the month, averages are all 0
            for status in possible_statuses:
                monthly_averages[status] = 0.0

        # 9. Assemble the final response data
        response_data = {
            "kelas_info": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                "totalSiswa": total_students
            },
            "month_info": {
                "year": year,
                "monthNumber": month,
                "monthName": {
                     1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                     5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                     9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                 }.get(month, ""),
                 "startDate": start_date_month.strftime('%Y-%m-%d'),
                 "endDate": end_date_month.strftime('%Y-%m-%d'),
                 "totalPossibleDaysInMonth": total_possible_days_in_month # Count of weekdays with records
            },
            "monthly_averages": monthly_averages,
            "daily_details": daily_details_list # This list includes details for every weekday in the month
        }

        return JsonResponse({
            "status": 200,
            "message": "Ringkasan kehadiran bulanan berhasil diambil",
            "data": response_data
        }, status=200)

    except Teacher.DoesNotExist:
        return JsonResponse({
            "status": 404,
            "errorMessage": "Profil guru tidak ditemukan."
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan internal saat mengambil ringkasan kehadiran: {str(e)}"
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_yearly_attendance_summary(request, kelas_id):
    """
    Get yearly attendance summary with monthly and weekly breakdowns for a specific class.
    Optional query parameter 'year' (defaults to current year).
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
            return JsonResponse({
                "status": 404,
                "errorMessage": "Kelas tidak ditemukan, tidak aktif, atau Anda bukan wali kelas untuk kelas ini."
            }, status=404)

        # 3. Get and validate year from query parameters
        year_param = request.query_params.get('year', str(timezone.now().year))
        try:
            year = int(year_param)
            if year < 2000 or year > timezone.now().year + 5:
                return JsonResponse({
                    "status": 400,
                    "errorMessage": f"Parameter 'year' tidak valid. Gunakan tahun yang masuk akal (cth. 2000 - {timezone.now().year + 5})."
                }, status=400)
        except ValueError:
            return JsonResponse({
                "status": 400,
                "errorMessage": "Parameter 'year' harus berupa angka valid."
            }, status=400)

        # 4. Initialize response structure
        monthly_summaries = []
        total_students = kelas.siswa.count()
        possible_statuses = ['Hadir', 'Sakit', 'Izin', 'Alfa']
        indonesian_days = {
            0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat"
        }
        indonesian_months = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }

        # 5. Process each month
        for month in range(1, 13):
            try:
                # Get the date range for this month
                start_date_month = date(year, month, 1)
                last_day_of_month = calendar.monthrange(year, month)[1]
                end_date_month = date(year, month, last_day_of_month)

                # Get all attendance records for weekdays in this month
                monthly_records = AbsensiHarian.objects.filter(
                    kelas=kelas,
                    date__year=year,
                    date__month=month,
                    date__week_day__range=(2, 6)  # Mon-Fri
                ).order_by('date')

                # Skip months with no records
                if not monthly_records.exists():
                    continue

                # Initialize monthly totals
                monthly_total_counts = defaultdict(int)
                weekly_summaries = []

                # Group records by week
                weekly_records = {}
                for record in monthly_records:
                    week_num = ((record.date.day - 1) // 7) + 1
                    if week_num not in weekly_records:
                        weekly_records[week_num] = []
                    weekly_records[week_num].append(record)

                # Process each week
                for week_num, week_records in weekly_records.items():
                    if not week_records:
                        continue

                    week_start = week_records[0].date
                    week_end = week_records[-1].date
                    weekly_total_counts = defaultdict(int)
                    daily_details = {}

                    # Initialize daily details for this week (Mon-Fri)
                    current_day = week_start
                    while current_day <= week_end:
                        if current_day.weekday() < 5:
                            date_str = current_day.strftime('%Y-%m-%d')
                            daily_details[date_str] = {
                                "day_name": indonesian_days[current_day.weekday()],
                                "date": date_str,
                                "attendance_percentage": 0.0,
                                "counts": {status: 0 for status in possible_statuses},
                                "has_record": False
                            }
                        current_day += timedelta(days=1)

                    # Process each day's records in this week
                    for record in week_records:
                        date_str = record.date.strftime('%Y-%m-%d')
                        if date_str in daily_details:
                            daily_details[date_str]["has_record"] = True
                            day_counts = defaultdict(int)

                            for student_id_key, data in record.listSiswa.items():
                                status = data.get("status", data) if isinstance(data, dict) else data
                                if status in possible_statuses:
                                    day_counts[status] += 1
                                    weekly_total_counts[status] += 1
                                    monthly_total_counts[status] += 1

                            daily_details[date_str]["counts"] = dict(day_counts)
                            hadir_count = day_counts.get("Hadir", 0)
                            daily_details[date_str]["attendance_percentage"] = round(
                                (hadir_count / total_students) * 100, 1
                            ) if total_students > 0 else 0.0

                    # Calculate weekly averages
                    total_weekly_slots = total_students * len(week_records)
                    weekly_averages = {}
                    if total_weekly_slots > 0:
                        raw_percentages = {}
                        total_raw_percentage = 0
                        for status in possible_statuses:
                            raw_percentage = (weekly_total_counts[status] / total_weekly_slots) * 100
                            raw_percentages[status] = raw_percentage
                            total_raw_percentage += raw_percentage

                        # Normalize to ensure sum is 100%
                        if total_raw_percentage > 0:
                            for status in possible_statuses:
                                weekly_averages[status] = round(
                                    (raw_percentages[status] / total_raw_percentage) * 100, 1
                                )
                        else:
                            weekly_averages = {status: 0.0 for status in possible_statuses}
                    else:
                        weekly_averages = {status: 0.0 for status in possible_statuses}

                    # Format the display date range
                    start_day = week_start.day
                    end_day = week_end.day
                    start_month_name = indonesian_months[week_start.month]
                    end_month_name = indonesian_months[week_end.month]
                    
                    if week_start.month == week_end.month:
                        # Same month: "6 - 10 January"
                        display_date_range = f"{start_day} - {end_day} {start_month_name}"
                    else:
                        # Different months: "31 March - 4 April"
                        display_date_range = f"{start_day} {start_month_name} - {end_day} {end_month_name}"

                    # Add weekly summary
                    weekly_summaries.append({
                        "week_info": {
                            "startDate": week_start.strftime('%Y-%m-%d'),
                            "endDate": week_end.strftime('%Y-%m-%d'),
                            "displayWeek": f"Minggu {week_num}: {display_date_range}"
                        },
                        "weekly_averages": weekly_averages,
                        "daily_details": sorted(
                            [details for details in daily_details.values()],
                            key=lambda x: x['date']
                        )
                    })

                # Calculate monthly averages
                total_monthly_slots = total_students * len(monthly_records)
                monthly_averages = {}
                if total_monthly_slots > 0:
                    raw_percentages = {}
                    total_raw_percentage = 0
                    for status in possible_statuses:
                        raw_percentage = (monthly_total_counts[status] / total_monthly_slots) * 100
                        raw_percentages[status] = raw_percentage
                        total_raw_percentage += raw_percentage

                    # Normalize to ensure sum is 100%
                    if total_raw_percentage > 0:
                        for status in possible_statuses:
                            monthly_averages[status] = round(
                                (raw_percentages[status] / total_raw_percentage) * 100, 1
                            )
                    else:
                        monthly_averages = {status: 0.0 for status in possible_statuses}
                else:
                    monthly_averages = {status: 0.0 for status in possible_statuses}

                # Add monthly summary
                monthly_summaries.append({
                    "month_info": {
                        "year": year,
                        "monthNumber": month,
                        "monthName": indonesian_months[month],
                        "startDate": start_date_month.strftime('%Y-%m-%d'),
                        "endDate": end_date_month.strftime('%Y-%m-%d'),
                        "totalDays": len(monthly_records)
                    },
                    "monthly_averages": monthly_averages,
                    "weekly_summaries": weekly_summaries
                })

            except Exception as e:
                print(f"Error processing month {month}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        # 6. Prepare final response
        response_data = {
            "kelas_info": {
                "id": kelas.id,
                "namaKelas": re.sub(r'^Kelas\s+', '', kelas.namaKelas, flags=re.IGNORECASE) if kelas.namaKelas else None,
                "waliKelas": kelas.waliKelas.name if kelas.waliKelas else None,
                "totalSiswa": total_students
            },
            "year": year,
            "monthly_summaries": monthly_summaries
        }

        return JsonResponse({
            "status": 200,
            "message": "Ringkasan kehadiran tahunan berhasil diambil",
            "data": response_data
        }, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": 500,
            "errorMessage": f"Terjadi kesalahan internal: {str(e)}"
        }, status=500)