from django.http import JsonResponse
from django.shortcuts import render
from .models import *
from kelas.models import *
from user.models import Student
from rest_framework.decorators import api_view, permission_classes
import re
from rest_framework.permissions import IsAuthenticated, BasePermission
# Create your views here.

class IsStudentRole(BasePermission):
    """
    only allow users with role 'admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')

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


