from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from .models import Nilai
from .serializers import NilaiSerializer
import json
from decimal import Decimal, InvalidOperation
import traceback
from matapelajaran.models import MataPelajaran
from komponenpenilaian.models import KomponenPenilaian
from user.models import Teacher, Student, User
from kelas.models import Kelas
import json
from decimal import Decimal, InvalidOperation
import traceback
from matapelajaran.models import MataPelajaran
from komponenpenilaian.models import KomponenPenilaian
from user.models import Teacher, Student, User
from nilai.models import Nilai
from kelas.models import Kelas

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_nilai(request):
    """Create a new nilai (grade) entry"""
    try:
        serializer = NilaiSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 201,
                "message": "Nilai created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": 400,
            "message": "Invalid data provided",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error creating nilai: {str(e)}",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nilai_by_matapelajaran(request, matapelajaran_id):
    """Get all nilai entries for a specific mata pelajaran"""
    try:
        nilai_list = Nilai.objects.filter(matapelajaran_id=matapelajaran_id)
        serializer = NilaiSerializer(nilai_list, many=True)
        return Response({
            "status": 200,
            "message": "Successfully retrieved nilai list",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving nilai: {str(e)}",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nilai_by_student(request, student_id):
    """Get all nilai entries for a specific student"""
    try:
        nilai_list = Nilai.objects.filter(student_id=student_id)
        serializer = NilaiSerializer(nilai_list, many=True)
        return Response({
            "status": 200,
            "message": "Successfully retrieved nilai list",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error retrieving nilai: {str(e)}",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_nilai(request, nilai_id):
    """Update an existing nilai entry"""
    try:
        nilai = Nilai.objects.get(pk=nilai_id)
        serializer = NilaiSerializer(nilai, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 200,
                "message": "Nilai updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": 400,
            "message": "Invalid data provided",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Nilai.DoesNotExist:
        return Response({
            "status": 404,
            "message": "Nilai not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": 500,
            "message": f"Error updating nilai: {str(e)}",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Helper function
def drf_error_response(message, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({'message': message, 'error': True}, status=http_status)

# --- View grade_data_view (Sesuai Model Nilai Ideal) ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def grade_data_view(request: Request, matapelajaran_id: int):
    """
    Handles GET/POST for grade data using the CORRECTED Nilai model.
    GET: Returns per-component grades accurately.
    POST: Saves/Updates grade for a specific student and component.
    """
    # --- Dapatkan profil Guru & MataPelajaran, Cek Permission (SAMA) ---
    try: requesting_teacher = request.user.teacher
    except (Teacher.DoesNotExist, AttributeError): return drf_error_response("Akses ditolak.", status.HTTP_403_FORBIDDEN)
    try: matapelajaran = MataPelajaran.objects.select_related('teacher__user', 'tahunAjaran').prefetch_related('siswa_terdaftar', 'komponenpenilaian_matpel').get(id=matapelajaran_id, isDeleted=False, isActive=True)
    except MataPelajaran.DoesNotExist: return drf_error_response(f"MatPel tidak ditemukan.", status.HTTP_404_NOT_FOUND)
    if matapelajaran.teacher and matapelajaran.teacher != requesting_teacher: return drf_error_response("Tidak ada izin.", status.HTTP_403_FORBIDDEN)

    # ==========================
    # --- Handle GET Request ---
    # ==========================
    if request.method == 'GET':
        try:
            # Ambil siswa & komponen (SAMA)
            students_queryset = matapelajaran.siswa_terdaftar.filter(isDeleted=False, isActive=True); students_list = []
            for sp in students_queryset: k = Kelas.objects.filter(siswa=sp).first(); students_list.append({"id": str(sp.user_id), "name": sp.name or sp.user.username, "class": k.namaKelas if k else "N/A"})
            assessment_components_qs = matapelajaran.komponenpenilaian_matpel.all(); assessment_components_formatted = [{'id': str(c.id), 'name': c.namaKomponen, 'weight': c.bobotKomponen} for c in assessment_components_qs]

            # --- Ambil initialGrades (Logika Benar untuk Model Baru) ---
            initial_grades = {}
            if students_list and assessment_components_formatted:
                student_user_ids_str = [s['id'] for s in students_list]; component_ids = [comp.id for comp in assessment_components_qs]
                # Ambil record Nilai yang relevan
                nilai_records = Nilai.objects.filter(student_id__in=student_user_ids_str, komponen_id__in=component_ids).values('student_id', 'komponen_id', 'nilai')
                # Buat map untuk lookup cepat
                grades_map = {}
                for record in nilai_records:
                    sid = str(record['student_id']); cid = str(record['komponen_id']); score = record['nilai']; score_fl = float(score) if score is not None else None
                    if sid not in grades_map: grades_map[sid] = {}
                    grades_map[sid][cid] = score_fl
                # Isi initialGrades dari map
                for sd in students_list:
                    sid = sd['id']; initial_grades[sid] = {}
                    for comp in assessment_components_formatted: cid = comp['id']; initial_grades[sid][cid] = grades_map.get(sid, {}).get(cid, None) # Default null jika tidak ada
            else: # Buat struktur kosong jika tidak ada siswa/komponen
                 for sd in students_list: initial_grades[sd['id']] = {comp['id']: None for comp in assessment_components_formatted}
                  # --- TAMBAHKAN academicYear ke response_data ---
            academic_year_str = "N/A" # Default jika tidak ada
            if matapelajaran.tahunAjaran: # Cek apakah relasi tahunAjaran ada
                try:
                    # Ambil nilai integer tahun dari objek TahunAjaran yang berelasi
                    academic_year_str = str(matapelajaran.tahunAjaran.tahunAjaran)
                except AttributeError:
                    # Fallback jika objek TahunAjaran tidak punya field 'tahunAjaran' (seharusnya tidak terjadi)
                    print(f"Warning: Field 'tahunAjaran' tidak ditemukan pada objek TahunAjaran ID {matapelajaran.tahunAjaran_id}")
                    academic_year_str = f"ID {matapelajaran.tahunAjaran_id}"
            teacher_name = "" # Default null jika matpel tidak punya guru
            teacher_nisp = ""
            if matapelajaran.teacher:
                 # Ambil ID dari user yang berelasi dengan teacher (karena PK Teacher = User ID)
                 teacher_name = str(matapelajaran.teacher.name)
                 teacher_nisp = str(matapelajaran.teacher.nisp)

            response_data = {
                "students": students_list,
                "assessmentComponents": assessment_components_formatted,
                "subjectName": matapelajaran.nama,
                "initialGrades": initial_grades,
                "academicYear": academic_year_str,
                "teacherName": teacher_name,
                "teacherNisp": teacher_nisp
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e: print(f"...Error GET: {e}"); traceback.print_exc(); return drf_error_response("Error internal GET.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ===========================
    # --- Handle POST Request ---
    # ===========================
    elif request.method == 'POST':
        try:
            # Parsing & Validasi Input (SAMA)
            data = request.data; student_user_id = data.get('studentId'); component_id = data.get('componentId'); score_input = data.get('score')
            if not all(k in data for k in ['studentId', 'componentId', 'score']) or not student_user_id or not component_id: return drf_error_response("Data tidak lengkap.", status.HTTP_400_BAD_REQUEST)

            # Konversi & Validasi Score (SAMA)
            final_score = None
            if score_input is not None and str(score_input).strip() != '':
                try: numeric_score = Decimal(str(score_input)); assert 0 <= numeric_score <= 100; final_score = numeric_score
                except: return drf_error_response(f"Skor tidak valid.", status.HTTP_400_BAD_REQUEST)

            # Validasi Siswa (ambil User object - SAMA)
            try: student_profile = Student.objects.select_related('user').get(user_id=str(student_user_id)); student_user = student_profile.user
            except Student.DoesNotExist: return drf_error_response(f"Siswa tidak ditemukan.", status.HTTP_404_NOT_FOUND)
            if not matapelajaran.siswa_terdaftar.filter(user_id=student_user.id).exists(): return drf_error_response(f"Siswa tidak terdaftar.", status.HTTP_400_BAD_REQUEST)

            # Validasi Komponen (SAMA)
            try: komponen = KomponenPenilaian.objects.get(id=str(component_id), mataPelajaran=matapelajaran)
            except KomponenPenilaian.DoesNotExist: return drf_error_response(f"Komponen tidak valid.", status.HTTP_400_BAD_REQUEST)

            # --- Simpan/Update Nilai (Logika Benar untuk Model Baru) ---
            try:
                # update_or_create berdasarkan student (User) dan komponen
                nilai_obj, created = Nilai.objects.update_or_create(
                    student=student_user,   # Kunci 1: Object User
                    komponen=komponen,    # Kunci 2: Object KomponenPenilaian
                    defaults={'nilai': final_score} # Update field nilai
                )
                action = "dibuat" if created else "diperbarui"
                return Response({ # Gunakan Response DRF
                    "message": f"Nilai untuk komponen '{komponen.namaKomponen}' berhasil {action}.",
                    "studentId": str(student_user_id),
                    "componentId": str(component_id), # Kembalikan componentId
                    'savedScore': float(final_score) if final_score is not None else None
                }, status=status.HTTP_200_OK)
            # --- AKHIR Simpan ---
            except Exception as e: print(f"...Error saving Nilai: {e}"); return drf_error_response("Gagal menyimpan nilai.", status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e: print(f"...Error POST: {e}"); traceback.print_exc(); return drf_error_response("Error internal POST.", status.HTTP_500_INTERNAL_SERVER_ERROR)

# Helper function
def drf_error_response(message, http_status=status.HTTP_400_BAD_REQUEST): # <-- Menggunakan modul status
    return Response({'message': message, 'error': True}, status=http_status)


# --- View get_teacher_subjects_summary (Variabel diganti) ---
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_teacher_subjects_summary(request: Request):
    # ... (Logika get teacher SAMA) ...
    try: logged_in_teacher = request.user.teacher
    except (Teacher.DoesNotExist, AttributeError): return drf_error_response("Akses ditolak.", status=status.HTTP_403_FORBIDDEN) # <-- Menggunakan modul status

    print(f"[API GET /api/nilai/subjects/] Fetching summary for teacher: {logged_in_teacher.user.username}")
    try:
        active_subjects = MataPelajaran.objects.filter(teacher=logged_in_teacher, isDeleted=False, isActive=True).prefetch_related('komponenpenilaian_matpel', 'siswa_terdaftar').select_related('tahunAjaran')
        summary_list = []
        for subject in active_subjects:
            components = subject.komponenpenilaian_matpel.all(); students_qs = subject.siswa_terdaftar.filter(isActive=True, isDeleted=False)
            component_count = components.count(); total_weight = sum(comp.bobotKomponen for comp in components if comp.bobotKomponen is not None); student_count = students_qs.count()

            # --- GANTI NAMA VARIABEL LOKAL ---
            subject_status = 'Belum Dimulai' # <<< Ganti nama variabel ini
            # ----------------------------------
            total_possible_entries = student_count * component_count
            if total_possible_entries > 0 :
                student_user_ids = students_qs.values_list('user_id', flat=True); component_ids = components.values_list('id', flat=True)
                filled_count = Nilai.objects.filter(student_id__in=student_user_ids, komponen_id__in=component_ids).count()

                if filled_count == total_possible_entries:
                     subject_status = 'Terisi Penuh' # <<< Gunakan nama baru
                elif filled_count > 0:
                     subject_status = 'Dalam Proses' # <<< Gunakan nama baru

            components_data = [{'id': str(comp.id), 'name': comp.namaKomponen, 'weight': comp.bobotKomponen} for comp in components]
            summary_list.append({
                "id": str(subject.id), "subjectId": subject.kode, "name": subject.nama,
                "academicYear": str(subject.tahunAjaran.tahunAjaran) if subject.tahunAjaran else "N/A",
                "totalWeight": total_weight, "componentCount": component_count,
                "studentCount": student_count,
                # --- Gunakan nama baru di response ---
                "status": subject_status, # <<< Gunakan nama baru
                # ------------------------------------
                "components": components_data
            })

        return Response(summary_list, status=status.HTTP_200_OK) # <-- Menggunakan modul status

    except Exception as e:
        print(f"[API GET /api/nilai/subjects/] Error for teacher {logged_in_teacher.user.username}: {e}")
        traceback.print_exc()
        # Sekarang bisa panggil drf_error_response dengan benar
        return drf_error_response("Kesalahan Server Internal saat mengambil summary.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR) # <-- Menggunakan modul status
