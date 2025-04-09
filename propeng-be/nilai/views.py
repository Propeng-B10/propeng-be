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



# Helper function (tetap sama)
def drf_error_response(message, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({'message': message, 'error': True}, status=http_status)

# --- View grade_data_view (SETELAH PERUBAHAN) ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def grade_data_view(request: Request, matapelajaran_id: int):
    """
    Handles GET/POST for grade data using the CORRECTED Nilai model.
    GET: Returns per-component grades separated by type ('initialGrades' and 'initialGrades_keterampilan').
    POST: Saves/Updates grade for a specific student, component, and scoreType.
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
            students_queryset = matapelajaran.siswa_terdaftar.filter(isDeleted=False, isActive=True)
            students_list = []
            for sp in students_queryset:
                # Pastikan user relation di Student tidak null
                if sp.user:
                    k = Kelas.objects.filter(siswa=sp).first()
                    students_list.append({
                        "id": str(sp.user_id),
                        "name": sp.name or sp.user.username, # Fallback ke username jika name null
                        "class": k.namaKelas if k else "N/A"
                    })
                else:
                    print(f"Warning: Siswa dengan ID {sp.id} tidak memiliki relasi user.")


            assessment_components_qs = matapelajaran.komponenpenilaian_matpel.all()
            assessment_components_formatted = [{'id': str(c.id), 'name': c.namaKomponen, 'weight': c.bobotKomponen} for c in assessment_components_qs]

            # --- Ambil initialGrades dengan struktur DUA KEY ---
            initial_grades_p = {} # Untuk Pengetahuan
            initial_grades_k = {} # Untuk Keterampilan

            if students_list and assessment_components_formatted:
                student_user_ids_str = [s['id'] for s in students_list]
                # Gunakan ID numerik untuk query, tapi string untuk key dict
                component_ids_int = [c.id for c in assessment_components_qs]

                # --- Inisialisasi kedua dictionary agar semua student/component ada ---
                for sd in students_list:
                    sid = sd['id']
                    initial_grades_p[sid] = {comp['id']: None for comp in assessment_components_formatted}
                    initial_grades_k[sid] = {comp['id']: None for comp in assessment_components_formatted}
                # --------------------------------------------------------------------

                # Ambil record Nilai yang relevan TERMASUK tipe_nilai
                nilai_records = Nilai.objects.filter(
                    student_id__in=student_user_ids_str,
                    komponen_id__in=component_ids_int # Gunakan ID int untuk query
                ).values('student_id', 'komponen_id', 'nilai', 'tipe_nilai') # <-- Tambah tipe_nilai

                # Isi dictionary berdasarkan tipe
                for record in nilai_records:
                    sid = str(record['student_id'])
                    cid = str(record['komponen_id']) # Gunakan ID string untuk key dict
                    tipe = record['tipe_nilai']
                    score = record['nilai']
                    score_fl = float(score) if score is not None else None

                    # Cek apakah student ID ada di map (harusnya ada dari inisialisasi)
                    if sid not in initial_grades_p or sid not in initial_grades_k:
                         print(f"Warning: Student ID {sid} dari Nilai tidak ditemukan di students_list.")
                         continue # Lewati jika siswa tidak ada dalam daftar kelas ini

                    if tipe == Nilai.PENGETAHUAN:
                        if cid in initial_grades_p[sid]: # Cek apakah komponen ID valid
                            initial_grades_p[sid][cid] = score_fl
                        else:
                             print(f"Warning: Component ID {cid} untuk Nilai Pengetahuan tidak ditemukan di assessment_components_formatted.")
                    elif tipe == Nilai.KETERAMPILAN:
                        if cid in initial_grades_k[sid]: # Cek apakah komponen ID valid
                             initial_grades_k[sid][cid] = score_fl
                        else:
                             print(f"Warning: Component ID {cid} untuk Nilai Keterampilan tidak ditemukan di assessment_components_formatted.")


            # --- Dapatkan info lain (SAMA) ---
            academic_year_str = "N/A"
            if matapelajaran.tahunAjaran:
                try: academic_year_str = str(matapelajaran.tahunAjaran.tahunAjaran)
                except AttributeError: print(f"Warning: Field 'tahunAjaran' tidak ditemukan pada objek TahunAjaran ID {matapelajaran.tahunAjaran_id}"); academic_year_str = f"ID {matapelajaran.tahunAjaran_id}"
            teacher_name = "" ; teacher_nisp = ""
            if matapelajaran.teacher:
                try: teacher_name = str(matapelajaran.teacher.name) if matapelajaran.teacher.name else str(matapelajaran.teacher.user.username) # Fallback ke username
                except AttributeError: teacher_name = "Error Nama Guru"
                try: teacher_nisp = str(matapelajaran.teacher.nisp)
                except AttributeError: teacher_nisp = "Error NISP"

            # --- Susun response_data dengan DUA key nilai ---
            response_data = {
                "students": students_list,
                "assessmentComponents": assessment_components_formatted,
                "subjectName": matapelajaran.nama,
                "initialGrades": initial_grades_p,                # <-- Key untuk Pengetahuan
                "initialGrades_keterampilan": initial_grades_k,  # <-- Key baru untuk Keterampilan
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
            # Parsing & Validasi Input (TAMBAH scoreType)
            data = request.data
            student_user_id = data.get('studentId')
            component_id = data.get('componentId')
            score_input = data.get('score')
            tipe_nilai_input = data.get('scoreType') # <-- Terima tipe nilai

            # Validasi tipe_nilai_input
            if not tipe_nilai_input or tipe_nilai_input not in [Nilai.PENGETAHUAN, Nilai.KETERAMPILAN]:
                 return drf_error_response("Tipe nilai (scoreType='pengetahuan' atau 'keterampilan') tidak valid atau kosong.", status.HTTP_400_BAD_REQUEST)

            # Validasi input lain (tambahkan scoreType)
            if not all(k in data for k in ['studentId', 'componentId', 'score', 'scoreType']) or not student_user_id or not component_id:
                 return drf_error_response("Data tidak lengkap (membutuhkan studentId, componentId, score, scoreType).", status.HTTP_400_BAD_REQUEST)

            # Konversi & Validasi Score (SAMA)
            final_score = None
            if score_input is not None and str(score_input).strip() != '':
                try: numeric_score = Decimal(str(score_input)); assert 0 <= numeric_score <= 100; final_score = numeric_score
                except: return drf_error_response(f"Skor tidak valid (harus angka antara 0-100 atau kosong/null).", status.HTTP_400_BAD_REQUEST)

            # Validasi Siswa (ambil User object - SAMA)
            try: student_profile = Student.objects.select_related('user').get(user_id=str(student_user_id)); student_user = student_profile.user
            except Student.DoesNotExist: return drf_error_response(f"Siswa tidak ditemukan.", status.HTTP_404_NOT_FOUND)
            if not matapelajaran.siswa_terdaftar.filter(user=student_user).exists(): return drf_error_response(f"Siswa tidak terdaftar pada mata pelajaran ini.", status.HTTP_400_BAD_REQUEST)

            # Validasi Komponen (SAMA)
            try: komponen = KomponenPenilaian.objects.get(id=str(component_id), mataPelajaran=matapelajaran)
            except KomponenPenilaian.DoesNotExist: return drf_error_response(f"Komponen penilaian tidak valid untuk mata pelajaran ini.", status.HTTP_400_BAD_REQUEST)

            # --- Simpan/Update Nilai (Gunakan tipe_nilai) ---
            try:
                # update_or_create berdasarkan student, komponen, DAN tipe_nilai
                nilai_obj, created = Nilai.objects.update_or_create(
                    student=student_user,           # Kunci 1: Object User
                    komponen=komponen,            # Kunci 2: Object KomponenPenilaian
                    tipe_nilai=tipe_nilai_input,  # <-- Kunci 3: Tipe Nilai dari request
                    defaults={'nilai': final_score} # Update field nilai
                )
                action = "dibuat" if created else "diperbarui"
                return Response({ # Gunakan Response DRF
                    "message": f"Nilai {tipe_nilai_input} untuk komponen '{komponen.namaKomponen}' berhasil {action}.",
                    "studentId": str(student_user_id),
                    "componentId": str(component_id),
                    "scoreType": tipe_nilai_input, # Kembalikan tipe yg disimpan
                    'savedScore': float(final_score) if final_score is not None else None
                }, status=status.HTTP_200_OK)
            # --- AKHIR Simpan ---
            except Exception as e:
                 print(f"...Error saving Nilai: {e}")
                 traceback.print_exc() # Cetak traceback untuk debug
                 return drf_error_response(f"Gagal menyimpan nilai: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(f"...Error POST: {e}")
            traceback.print_exc()
            return drf_error_response("Error internal POST.", status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- View get_teacher_subjects_summary (SETELAH PERUBAHAN) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Uncomment jika perlu otentikasi
def get_teacher_subjects_summary(request: Request):
    # ... (Logika get teacher SAMA) ...
    try: logged_in_teacher = request.user.teacher
    except (Teacher.DoesNotExist, AttributeError): return drf_error_response("Akses guru ditolak.", status.HTTP_403_FORBIDDEN)

    print(f"[API GET /api/nilai/subjects/] Fetching summary for teacher: {logged_in_teacher.user.username}")
    try:
        active_subjects = MataPelajaran.objects.filter(
            teacher=logged_in_teacher, isDeleted=False, isActive=True
        ).prefetch_related(
            'komponenpenilaian_matpel', 'siswa_terdaftar__user' # Prefetch user siswa juga
        ).select_related('tahunAjaran', 'teacher__user') # Prefetch user guru

        summary_list = []
        for subject in active_subjects:
            components = subject.komponenpenilaian_matpel.all()
            # Filter siswa terdaftar yang aktif & tidak dihapus
            students_qs = subject.siswa_terdaftar.filter(isActive=True, isDeleted=False)

            component_count = components.count()
            total_weight = sum(comp.bobotKomponen for comp in components if comp.bobotKomponen is not None)
            student_count = students_qs.count()

            # Status Awal
            subject_status = 'Belum Dimulai'

            # Perhitungan Status (SUDAH DISESUAIKAN)
            # Asumsi setiap komponen idealnya memiliki 2 tipe nilai (P & K)
            total_possible_entries = student_count * component_count * 2 # <-- Dikalikan 2

            if total_possible_entries > 0 :
                # Ambil ID user siswa yang valid
                student_user_ids = [s.user_id for s in students_qs if s.user_id] # Pastikan user_id ada
                component_ids = components.values_list('id', flat=True)

                if student_user_ids and component_ids: # Hanya query jika ada ID siswa dan komponen
                    # filled_count tetap menghitung jumlah record Nilai yang ada
                    filled_count = Nilai.objects.filter(
                        student_id__in=student_user_ids,
                        komponen_id__in=component_ids
                    ).count()

                    # Logika status menggunakan total_possible_entries yang baru
                    if filled_count == total_possible_entries:
                         subject_status = 'Terisi Penuh'
                    elif filled_count > 0:
                         subject_status = 'Dalam Proses'
                    # Jika filled_count == 0, status tetap 'Belum Dimulai'
                else:
                     # Jika tidak ada siswa atau komponen, status tetap 'Belum Dimulai'
                     pass


            components_data = [{'id': str(comp.id), 'name': comp.namaKomponen, 'weight': comp.bobotKomponen} for comp in components]
            summary_list.append({
                "id": str(subject.id),
                "subjectId": subject.kode, # Asumsi ada field 'kode'
                "name": subject.nama,
                "academicYear": str(subject.tahunAjaran.tahunAjaran) if subject.tahunAjaran else "N/A",
                "totalWeight": total_weight,
                "componentCount": component_count,
                "studentCount": student_count,
                "status": subject_status, # <-- Status yang sudah dihitung
                "components": components_data
            })

        return Response(summary_list, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[API GET /api/nilai/subjects/] Error for teacher {logged_in_teacher.user.username}: {e}")
        traceback.print_exc()
        return drf_error_response("Kesalahan Server Internal saat mengambil summary.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
