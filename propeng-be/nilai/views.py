from statistics import mean
from capaiankompetensi.models import CapaianKompetensi
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from .models import Nilai
from .serializers import NilaiSerializer
import json
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
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
from komponenpenilaian.models import KomponenPenilaian, PENGETAHUAN, KETERAMPILAN
from collections import Counter, defaultdict
from django.db.models import Avg, Count, Case, When, IntegerField

KKM = 75

def get_grade(nilai):
    if nilai >= 93:
        return 'a'
    elif nilai >= 84:
        return 'b'
    elif nilai >= 75:
        return 'c'
    else:
        return 'd'

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

# --- View grade_data_view (SETELAH PERUBAHAN BESAR) ---
@api_view(['GET', 'POST'])
def grade_data_view(request: Request, matapelajaran_id: int):
    """
    Handles GET/POST for grade data.
    GET: Returns students, all components (with type), and a single initialGrades dict.
    POST: Saves/Updates grade for a specific student and component (type is inherent in component).
    """
    # --- Dapatkan profil Guru & MataPelajaran, Cek Permission (SAMA) ---
    requesting_teacher = None
    if request.user.is_authenticated:
        try: 
            requesting_teacher = request.user.teacher
        except (Teacher.DoesNotExist, AttributeError): 
            pass  # Allow access even if not a teacher

    try:
        # Prefetch komponen penilaian
        matapelajaran = MataPelajaran.objects.select_related('teacher__user', 'tahunAjaran').prefetch_related(
            'siswa_terdaftar__user', # Include user relation for student
            'komponenpenilaian_matpel' # Prefetch components
        ).get(id=matapelajaran_id, isDeleted=False, isActive=True)
    except MataPelajaran.DoesNotExist: 
        return drf_error_response(f"MatPel tidak ditemukan.", status.HTTP_404_NOT_FOUND)

    # Only check teacher permissions for POST requests
    if request.method == 'POST':
        if not requesting_teacher:
            return drf_error_response("Akses ditolak. Hanya guru yang dapat mengubah nilai.", status.HTTP_403_FORBIDDEN)
        if matapelajaran.teacher and matapelajaran.teacher != requesting_teacher:
            siswa_ids = matapelajaran.siswa_terdaftar.values_list("id", flat=True)
            wali_kelas_kelas = Kelas.objects.filter(
                siswa__in=siswa_ids,
                waliKelas=requesting_teacher,
                isActive=True,
                isDeleted=False
            ).distinct()

            if not wali_kelas_kelas.exists():
                return drf_error_response("Tidak ada izin.", status.HTTP_403_FORBIDDEN)
    
    # ==========================
    # --- Handle GET Request ---
    # ==========================
    if request.method == 'GET':
        try:
            # Ambil siswa (SAMA, pastikan user ada)
            students_queryset = matapelajaran.siswa_terdaftar.filter(isDeleted=False, isActive=True)
            students_list = []
            student_user_ids_str = [] # Kumpulkan ID string untuk dictionary key
            student_user_ids_int = [] # Kumpulkan ID int untuk query Nilai

            for sp in students_queryset:
                if sp.user:
                    k = Kelas.objects.filter(siswa=sp).first()
                    student_id_str = str(sp.user_id)
                    students_list.append({
                        "id": student_id_str,
                        "name": sp.name or sp.user.username,
                        "class": k.namaKelas if k else "N/A"
                    })
                    student_user_ids_str.append(student_id_str)
                    student_user_ids_int.append(sp.user_id) # ID asli (int/UUID)
                else:
                    print(f"Warning: Siswa dengan ID {sp.id} tidak memiliki relasi user.")


            # Ambil SEMUA komponen penilaian, SERTAKAN TIPE
            assessment_components_qs = matapelajaran.komponenpenilaian_matpel.all()
            assessment_components_formatted = [{
                'id': str(c.id),
                'name': c.namaKomponen,
                'weight': c.bobotKomponen,
                'type': c.tipeKomponen # Sertakan tipe komponen di sini!
            } for c in assessment_components_qs]
            component_ids_int = [c.id for c in assessment_components_qs] # ID untuk query

            # --- Ambil initialGrades (SATU DICTIONARY) ---
            initial_grades = {}

            if students_list and assessment_components_formatted:
                # --- Inisialisasi dictionary agar semua student/component ada ---
                for sid in student_user_ids_str:
                    initial_grades[sid] = {comp['id']: None for comp in assessment_components_formatted}
                # --------------------------------------------------------------------

                # Ambil record Nilai yang relevan (TIDAK PERLU tipe_nilai)
                nilai_records = Nilai.objects.filter(
                    student_id__in=student_user_ids_int, # Query pakai ID asli
                    komponen_id__in=component_ids_int   # Query pakai ID asli
                ).values('student_id', 'komponen_id', 'nilai') # Hanya perlu field ini

                # Isi dictionary
                for record in nilai_records:
                    sid = str(record['student_id'])  # Key pakai string
                    cid = str(record['komponen_id']) # Key pakai string
                    score = record['nilai']
                    score_fl = float(score) if score is not None else None

                    # Cek apakah student dan komponen ada di map (harusnya ada)
                    if sid in initial_grades and cid in initial_grades[sid]:
                        initial_grades[sid][cid] = score_fl
                    else:
                         print(f"Warning: Kombinasi Student ID {sid} / Component ID {cid} dari Nilai tidak cocok.")


            # --- Dapatkan info lain (SAMA) ---
            academic_year_str = "N/A"
            if matapelajaran.tahunAjaran:
                 try: academic_year_str = str(matapelajaran.tahunAjaran.tahunAjaran)
                 except AttributeError: academic_year_str = f"ID {matapelajaran.tahunAjaran_id}" # Fallback
            teacher_name = matapelajaran.teacher.name if matapelajaran.teacher and matapelajaran.teacher.name else (matapelajaran.teacher.user.username if matapelajaran.teacher else "N/A")
            teacher_nisp = matapelajaran.teacher.nisp if matapelajaran.teacher else "N/A"

            # --- Susun response_data dengan SATU key nilai & komponen BERTIPE ---
            response_data = {
                "students": students_list,
                "assessmentComponents": assessment_components_formatted, # <-- Kirim ini ke frontend
                "subjectName": matapelajaran.nama,
                "initialGrades": initial_grades, # <-- Hanya satu dictionary nilai
                # "initialGrades_keterampilan": initial_grades_k, # <-- HAPUS INI
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
            # Parsing & Validasi Input (HAPUS scoreType)
            data = request.data
            student_user_id = data.get('studentId')
            component_id = data.get('componentId')
            score_input = data.get('score')
            # tipe_nilai_input = data.get('scoreType') # <-- HAPUS INI

            # Validasi tipe_nilai_input SUDAH TIDAK PERLU
            # if not tipe_nilai_input or tipe_nilai_input not in [Nilai.PENGETAHUAN, Nilai.KETERAMPILAN]: ...

            # Validasi input lain (tanpa scoreType)
            if not all(k in data for k in ['studentId', 'componentId', 'score']) or not student_user_id or not component_id:
                 return drf_error_response("Data tidak lengkap (membutuhkan studentId, componentId, score).", status.HTTP_400_BAD_REQUEST)

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

            # --- Simpan/Update Nilai (TANPA tipe_nilai) ---
            try:
                # update_or_create berdasarkan student dan komponen saja
                nilai_obj, created = Nilai.objects.update_or_create(
                    student=student_user,      # Kunci 1: Object User
                    komponen=komponen,         # Kunci 2: Object KomponenPenilaian
                    # tipe_nilai=tipe_nilai_input, # <-- HAPUS Kunci 3
                    defaults={'nilai': final_score} # Update field nilai
                )
                action = "dibuat" if created else "diperbarui"
                return Response({ # Gunakan Response DRF
                    "message": f"Nilai untuk komponen '{komponen.namaKomponen}' ({komponen.get_tipeKomponen_display()}) berhasil {action}.", # Sebutkan tipe dari komponen
                    "studentId": str(student_user_id),
                    "componentId": str(component_id),
                    # "scoreType": tipe_nilai_input, # <-- Hapus dari response
                    'savedScore': float(final_score) if final_score is not None else None
                }, status=status.HTTP_200_OK)
            # --- AKHIR Simpan ---
            except Exception as e:
                print(f"...Error saving Nilai: {e}")
                traceback.print_exc()
                return drf_error_response(f"Gagal menyimpan nilai: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(f"...Error POST: {e}")
            traceback.print_exc()
            return drf_error_response("Error internal POST.", status.HTTP_500_INTERNAL_SERVER_ERROR)

# Helper function untuk menentukan status berdasarkan count (DRY - Don't Repeat Yourself)
def calculate_status(filled_count: int, total_possible: int) -> str:
    """Menghitung status berdasarkan jumlah terisi dan total kemungkinan."""
    if total_possible <= 0:
        return 'Belum Dimulai' # Atau 'Tidak Berlaku' jika 0 komponen/siswa
    if filled_count == total_possible:
        return 'Terisi Penuh'
    elif filled_count > 0:
        return 'Dalam Proses'
    else: # filled_count == 0
        return 'Belum Dimulai'

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_subjects_summary(request: Request):
    try:
        logged_in_teacher = request.user.teacher
    except (Teacher.DoesNotExist, AttributeError):
        # Menggunakan helper drf_error_response jika ada, jika tidak gunakan Response biasa
        # return drf_error_response("Akses guru ditolak.", status.HTTP_403_FORBIDDEN)
        return Response({"message": "Akses guru ditolak."}, status=status.HTTP_403_FORBIDDEN)

    print(f"[API GET /api/nilai/subjects/] Fetching summary for teacher: {logged_in_teacher.user.username}")
    try:
        active_subjects = MataPelajaran.objects.filter(
            teacher=logged_in_teacher, isDeleted=False, isActive=True
        ).prefetch_related(
            # Prefetch komponen penilaian
            'komponenpenilaian_matpel',
             # Prefetch siswa dan user siswa
            'siswa_terdaftar',
            'siswa_terdaftar__user'
        ).select_related('tahunAjaran', 'teacher__user') # Prefetch tahun ajaran dan user guru

        summary_list = []
        for subject in active_subjects:
            # Ambil komponen dari hasil prefetch
            components = list(subject.komponenpenilaian_matpel.all()) # Ubah ke list agar bisa difilter ulang
            # Ambil siswa dari hasil prefetch, filter lagi yang aktif
            students_qs = subject.siswa_terdaftar.filter(isActive=True, isDeleted=False)

            student_count = students_qs.count()
            student_user_ids = [s.user_id for s in students_qs if s.user_id] # Ambil ID user siswa

            # Pisahkan komponen berdasarkan tipe
            pengetahuan_components = [comp for comp in components if comp.tipeKomponen == 'Pengetahuan']
            keterampilan_components = [comp for comp in components if comp.tipeKomponen == 'Keterampilan']

            # --- Hitung Status Pengetahuan ---
            pengetahuan_comp_count = len(pengetahuan_components)
            pengetahuan_comp_ids = [comp.id for comp in pengetahuan_components]
            total_possible_pengetahuan = student_count * pengetahuan_comp_count
            filled_pengetahuan_count = 0
            if total_possible_pengetahuan > 0 and student_user_ids and pengetahuan_comp_ids:
                 filled_pengetahuan_count = Nilai.objects.filter(
                     student_id__in=student_user_ids,
                     komponen_id__in=pengetahuan_comp_ids
                 ).count()
            status_pengetahuan = calculate_status(filled_pengetahuan_count, total_possible_pengetahuan)
            # --- Akhir Hitung Status Pengetahuan ---

            # --- Hitung Status Keterampilan ---
            keterampilan_comp_count = len(keterampilan_components)
            keterampilan_comp_ids = [comp.id for comp in keterampilan_components]
            total_possible_keterampilan = student_count * keterampilan_comp_count
            filled_keterampilan_count = 0
            if total_possible_keterampilan > 0 and student_user_ids and keterampilan_comp_ids:
                 filled_keterampilan_count = Nilai.objects.filter(
                     student_id__in=student_user_ids,
                     komponen_id__in=keterampilan_comp_ids
                 ).count()
            status_keterampilan = calculate_status(filled_keterampilan_count, total_possible_keterampilan)
            # --- Akhir Hitung Status Keterampilan ---

            # --- Hitung Status Keseluruhan (Opsional, tapi diminta dipertahankan) ---
            all_comp_count = len(components)
            all_comp_ids = [comp.id for comp in components]
            total_possible_overall = student_count * all_comp_count
            filled_overall_count = 0
            # Kita bisa menjumlahkan filled_pengetahuan_count + filled_keterampilan_count
            # JIKA DIJAMIN tidak ada tipe komponen lain. Lebih aman query ulang jika ada kemungkinan tipe lain.
            # Asumsi hanya ada Pengetahuan & Keterampilan untuk efisiensi:
            # filled_overall_count = filled_pengetahuan_count + filled_keterampilan_count
            # Jika ingin lebih aman (menghitung semua tipe):
            if total_possible_overall > 0 and student_user_ids and all_comp_ids:
                 filled_overall_count = Nilai.objects.filter(
                     student_id__in=student_user_ids,
                     komponen_id__in=all_comp_ids
                 ).count()
            status_overall = calculate_status(filled_overall_count, total_possible_overall)
            # --- Akhir Hitung Status Keseluruhan ---


            # Kalkulasi total bobot (tidak berubah)
            total_weight = sum(comp.bobotKomponen for comp in components if comp.bobotKomponen is not None)

            # Siapkan data komponen untuk response (tidak berubah)
            components_data = [{
                'id': str(comp.id),
                'name': comp.namaKomponen,
                'weight': comp.bobotKomponen,
                'type': comp.tipeKomponen
             } for comp in components]

            # Bangun dictionary response
            summary_list.append({
                "id": str(subject.id),
                "subjectId": subject.kode, # Pastikan field 'kode' ada di model MataPelajaran
                "name": subject.nama,
                "academicYear": str(subject.tahunAjaran.tahunAjaran) if subject.tahunAjaran else "N/A",
                "totalWeight": total_weight,          # Bobot total semua komponen
                "componentCount": all_comp_count,     # Jumlah total semua komponen
                "studentCount": student_count,
                "status": status_overall,             # Status Keseluruhan (lama)
                "statusPengetahuan": status_pengetahuan, # Status Baru: Pengetahuan
                "statusKeterampilan": status_keterampilan, # Status Baru: Keterampilan
                "components": components_data         # Daftar komponen
            })

        return Response(summary_list, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[API GET /api/nilai/subjects/] Error for teacher {logged_in_teacher.user.username}: {e}")
        traceback.print_exc()
        # Menggunakan helper drf_error_response jika ada, jika tidak gunakan Response biasa
        # return drf_error_response("Kesalahan Server Internal saat mengambil summary.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "Kesalahan Server Internal saat mengambil summary."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def calculate_weighted_average(grades_list):
    """
    Calculates the SUM of weighted points from a list of grade entries.
    Result = Sum( individual_score * (component_weight / 100) )
    Each entry should be a dictionary like: {'nilai': float/Decimal/None, 'bobot': int/None}
    """
    total_points = Decimal(0)
    # Optional: Keep track if any calculation was actually done
    calculation_performed = False

    for grade_entry in grades_list:
        nilai = grade_entry.get('nilai')
        bobot = grade_entry.get('bobot')

        # Only include if nilai is not None and bobot is valid
        if nilai is not None and isinstance(bobot, (int, float)) and bobot > 0:
            try:
                # Ensure values are Decimal
                nilai_decimal = Decimal(str(nilai))
                bobot_decimal = Decimal(str(bobot))

                # Calculate points contributed by this component
                # points = nilai * (bobot / 100)
                component_points = nilai_decimal * (bobot_decimal / Decimal(100))

                # Add to the total sum
                total_points += component_points
                calculation_performed = True # Mark that we added points

            except (TypeError, ValueError, InvalidOperation):
                # Skip if conversion fails
                print(f"Skipping invalid grade entry for point calculation: {grade_entry}")
                continue

    # If no valid grades/weights were processed, return None
    if not calculation_performed:
        return None

    # Round the final sum to 2 decimal places (or adjust as needed)
    final_sum = total_points.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return final_sum

# --- View Baru untuk Siswa Melihat Nilai ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_all_grades(request: Request):
    """
    Mengambil semua nilai (pengetahuan & keterampilan) untuk semua mata pelajaran
    yang diikuti oleh siswa yang sedang login dalam konteks kelas aktifnya.
    """
    try:
        # 1. Verifikasi User adalah Siswa
        user = request.user
        if user.role != 'student':
            return drf_error_response("Akses ditolak. Hanya untuk siswa.", status.HTTP_403_FORBIDDEN)

        try:
            student_profile = Student.objects.select_related('user').get(user=user)
            if not student_profile.isActive or student_profile.isDeleted:
                 return drf_error_response("Profil siswa tidak aktif.", status.HTTP_403_FORBIDDEN)
        except Student.DoesNotExist:
            return drf_error_response("Profil siswa tidak ditemukan.", status.HTTP_404_NOT_FOUND)

        # 2. Cari Kelas Aktif Siswa
        # Asumsi siswa hanya terdaftar di satu kelas aktif pada satu waktu
        kelas_aktif = Kelas.objects.filter(
            siswa=student_profile,
            isActive=True,
            isDeleted=False
        ).select_related('tahunAjaran').order_by('-tahunAjaran__tahunAjaran').first() # Ambil yg terbaru jika ada > 1

        if not kelas_aktif:
            return drf_error_response("Siswa tidak terdaftar di kelas aktif manapun.", status.HTTP_404_NOT_FOUND)
        if not kelas_aktif.tahunAjaran:
             return drf_error_response("Kelas aktif siswa tidak memiliki Tahun Ajaran.", status.HTTP_400_BAD_REQUEST)


        # 3. Ambil Semua Nilai Siswa 
        nilai_list = Nilai.objects.filter(
            student=user,
            komponen__mataPelajaran__tahunAjaran=kelas_aktif.tahunAjaran,
            komponen__mataPelajaran__siswa_terdaftar=student_profile,
            komponen__mataPelajaran__isActive=True,
            komponen__mataPelajaran__isDeleted=False
        ).select_related(
            'komponen__mataPelajaran',
            'komponen'
        ).order_by(
            'komponen__mataPelajaran__nama',
            'komponen__tipeKomponen',
            'komponen__namaKomponen'
        )

        # 4. Strukturisasi Data Hasil (Grouping - same as before)
        nilai_per_matpel_grouped = defaultdict(lambda: {
            'id': None, 'nama': None, 'kategori': None, 'kode': None,
            'capaian_pengetahuan': None, 'capaian_keterampilan': None,
            'pengetahuan': [], 'keterampilan': []
        })
        processed_matpel_ids = set()
        

        for nilai_record in nilai_list:
            komponen = nilai_record.komponen
            matpel = komponen.mataPelajaran
            matpel_id_str = str(matpel.id)

            # Fetch Capaian Kompetensi ONCE per subject (same as before)
            if matpel.id not in processed_matpel_ids:
                capaian_pengetahuan_desc = None
                capaian_keterampilan_desc = None
                capaian_qs = CapaianKompetensi.objects.filter(mata_pelajaran=matpel)
                for capaian in capaian_qs:
                    if capaian.tipe == CapaianKompetensi.PENGETAHUAN:
                        capaian_pengetahuan_desc = capaian.deskripsi
                    elif capaian.tipe == CapaianKompetensi.KETERAMPILAN:
                        capaian_keterampilan_desc = capaian.deskripsi
                nilai_per_matpel_grouped[matpel_id_str]['capaian_pengetahuan'] = capaian_pengetahuan_desc
                nilai_per_matpel_grouped[matpel_id_str]['capaian_keterampilan'] = capaian_keterampilan_desc
                processed_matpel_ids.add(matpel.id)

            # Isi detail matpel jika belum ada (same as before)
            if nilai_per_matpel_grouped[matpel_id_str]['id'] is None:
                nilai_per_matpel_grouped[matpel_id_str]['id'] = matpel_id_str
                nilai_per_matpel_grouped[matpel_id_str]['nama'] = matpel.nama
                nilai_per_matpel_grouped[matpel_id_str]['kategori'] = matpel.get_kategoriMatpel_display()
                nilai_per_matpel_grouped[matpel_id_str]['kode'] = matpel.kode

            # Siapkan data entri nilai (same as before)
            grade_entry = {
                'komponen': komponen.namaKomponen,
                'bobot': komponen.bobotKomponen,
                'nilai': float(nilai_record.nilai) if nilai_record.nilai is not None else None
            }

            # Masukkan ke list yang sesuai (same as before)
            if komponen.tipeKomponen == PENGETAHUAN:
                nilai_per_matpel_grouped[matpel_id_str]['pengetahuan'].append(grade_entry)
            elif komponen.tipeKomponen == KETERAMPILAN:
                nilai_per_matpel_grouped[matpel_id_str]['keterampilan'].append(grade_entry)

       # --- 5. Calculate Averages and Finalize List ---
        final_result_list = []
        for subject_data in nilai_per_matpel_grouped.values():
            # Calculate averages using the helper function
            rata_rata_p = calculate_weighted_average(subject_data['pengetahuan'])
            rata_rata_k = calculate_weighted_average(subject_data['keterampilan'])

            # Add averages to the subject dictionary
            subject_data['rata_rata_pengetahuan'] = float(rata_rata_p) if rata_rata_p is not None else None
            subject_data['rata_rata_keterampilan'] = float(rata_rata_k) if rata_rata_k is not None else None

            final_result_list.append(subject_data)
        # --- --- --- --- --- --- --- --- --- --- --- ---

        # 6. Prepare Final Response Data (same structure as before)
        response_data = {
            "siswa_info": {
                "id": str(user.id),
                "username": user.username,
                "nisn": student_profile.nisn if student_profile.nisn else "N/A",
                "nama": student_profile.name or user.username
            },
            "kelas": {
                "nama": kelas_aktif.namaKelas,
                "wali_kelas": kelas_aktif.waliKelas.name,
                "wali_kelas_nisp": kelas_aktif.waliKelas.nisp if kelas_aktif.waliKelas else "N/A",
                "tahun_ajaran": str(kelas_aktif.tahunAjaran),
                "angkatan": kelas_aktif.angkatan
            },
            "nilai_siswa": final_result_list # This list now includes averages
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error fetching student grades: {e}")
        traceback.print_exc()
        return drf_error_response("Terjadi kesalahan internal saat mengambil data nilai.", status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_student_insights(student_ids, tahunAjaran):
    nilai_queryset = Nilai.objects.select_related(
        'student',
        'komponen__mataPelajaran'
    ).filter(
        student__id__in=student_ids,
        komponen__mataPelajaran__tahunAjaran=tahunAjaran
    ).exclude(nilai__isnull=True)

    # Group by student → mataPelajaran → nilai
    student_matpel_grades = defaultdict(lambda: defaultdict(list))
    for nilai in nilai_queryset:
        matpel_id = nilai.komponen.mataPelajaran.id
        student_id = nilai.student.id
        student_matpel_grades[student_id][matpel_id].append(nilai.nilai)

    # Store per-student summaries
    per_student_summary = {}

    class_averages = []

    for student_id, matpel_map in student_matpel_grades.items():
        matpel_grades = {}
        grade_counts = {'a': 0, 'b': 0, 'c': 0, 'd': 0}
        total_grades = []

        for matpel_id, nilai_list in matpel_map.items():
            avg = sum(nilai_list) / len(nilai_list)
            total_grades.append(avg)

            grade = get_grade(avg)
            grade_counts[grade] += 1

        matpel_total = len(matpel_map)
        avg_all = sum(total_grades) / len(total_grades) if total_grades else 0
        class_averages.append(avg_all)

        passed_matpel = grade_counts['a'] + grade_counts['b'] + grade_counts['c']
        per_student_summary[student_id] = {
            'grade_counts': grade_counts,
            'total_matpel': matpel_total,
            'passed_matpel': passed_matpel,
            'avg': avg_all
        }

    # Compute class average
    class_avg = sum(class_averages) / len(class_averages) if class_averages else 0
    class_threshold = class_avg + ((100 - class_avg) / 2)

    # Initialize all counters
    insights = {
        'more_than_8_A': 0,
        'between_1_8_A': 0,
        'zero_A': 0,
        'more_than_5_C': 0,
        'between_1_5_C': 0,
        'zero_C': 0,
        'more_than_3_D': 0,
        'between_1_3_D': 0,
        'zero_D': 0,
        'passed_less_than_half': 0,
        'passed_half_to_all': 0,
        'passed_all': 0,
        'below_class_avg': 0,
        'between_avg_and_threshold': 0,
        'above_threshold': 0,
        'avg_below_75': 0,
        'avg_between_75_84': 0,
        'avg_84_or_more': 0
    }

    for student_data in per_student_summary.values():
        a = student_data['grade_counts']['a']
        c = student_data['grade_counts']['c']
        d = student_data['grade_counts']['d']
        total = student_data['total_matpel']
        passed = student_data['passed_matpel']
        avg = student_data['avg']

        # A-grade insights
        if a > 8:
            insights['more_than_8_A'] += 1
        elif 1 <= a <= 8:
            insights['between_1_8_A'] += 1
        else:
            insights['zero_A'] += 1

        # C-grade insights
        if c > 5:
            insights['more_than_5_C'] += 1
        elif 1 <= c <= 5:
            insights['between_1_5_C'] += 1
        else:
            insights['zero_C'] += 1

        # D-grade insights
        if d > 3:
            insights['more_than_3_D'] += 1
        elif 1 <= d <= 3:
            insights['between_1_3_D'] += 1
        else:
            insights['zero_D'] += 1

        # Passed subject insights
        if passed < (total / 2):
            insights['passed_less_than_half'] += 1
        elif passed >= (total / 2) and passed < total:
            insights['passed_half_to_all'] += 1
        elif passed == total:
            insights['passed_all'] += 1

        # Class average comparison
        if avg < class_avg:
            insights['below_class_avg'] += 1
        elif class_avg <= avg < class_threshold:
            insights['between_avg_and_threshold'] += 1
        else:
            insights['above_threshold'] += 1

        # Final avg benchmarks
        if avg < 75:
            insights['avg_below_75'] += 1
        elif 75 <= avg < 84:
            insights['avg_between_75_84'] += 1
        else:
            insights['avg_84_or_more'] += 1

    # Optional: include the class average in return
    insights['class_avg'] = round(class_avg, 2)
    insights['class_threshold'] = round(class_threshold, 2)

    return insights

def calculate_class_distribution(kelas_id):
    kelas = Kelas.objects.get(id=kelas_id)
    siswa_ids = kelas.siswa.values_list('user_id', flat=True)

    nilai_qs = Nilai.objects.filter(
        student_id__in=siswa_ids,
        komponen__mataPelajaran__tahunAjaran=kelas.tahunAjaran
    ).select_related(
        'komponen__mataPelajaran'
    )

    nilai_per_siswa = defaultdict(list)

    for nilai in nilai_qs:
        nilai_per_siswa[nilai.student.id].append(nilai.nilai)

    grade_counts = Counter()

    for nilai_list in nilai_per_siswa.values():
        if not nilai_list:
            continue
        avg_score = sum(nilai_list) / len(nilai_list)
        grade = get_grade(avg_score)
        grade_counts[grade.lower()] += 1

    return {
        'distribusi': dict(grade_counts),
    }

def calculate_subject_avg_and_distribution_all(kelas_id):
    result = []

    kelas = Kelas.objects.get(id=kelas_id)
    siswa_ids = kelas.siswa.values_list('user_id', flat=True)

    nilai_qs = Nilai.objects.filter(
        student_id__in=siswa_ids,
        komponen__mataPelajaran__tahunAjaran=kelas.tahunAjaran
    ).select_related(
        'komponen__mataPelajaran'
    )

    nilai_per_matpel = defaultdict(lambda: defaultdict(list))

    for nilai in nilai_qs:
        mp = nilai.komponen.mataPelajaran
        student_id = nilai.student.id
        nilai_per_matpel[mp][student_id].append(nilai.nilai)

    for mp, siswa_nilai_dict in nilai_per_matpel.items():
        total_scores = []
        grade_counts = Counter()
        siswa_counts = 0

        for student_id, nilai_list in siswa_nilai_dict.items():
            if not nilai_list:
                continue
            avg_score = sum(nilai_list) / len(nilai_list)
            grade = get_grade(avg_score)
            grade_counts[grade.lower()] += 1
            total_scores.append(avg_score)
            siswa_counts += 1

        overall_avg = sum(total_scores) / len(total_scores) if total_scores else 0

        result.append({
            'id_mata_pelajaran': mp.id,
            'mata_pelajaran': mp.nama,
            'jumlah_siswa': siswa_counts,
            'rata_rata': round(overall_avg, 2),
            'distribusi': dict(grade_counts)
        })

    return result

def calculate_subject_avg_and_distribution_by_jenis(kelas_id):
    result = []

    kelas = Kelas.objects.get(id=kelas_id)
    siswa_ids = kelas.siswa.values_list('user_id', flat=True)

    nilai_qs = Nilai.objects.filter(
        student_id__in=siswa_ids,
        komponen__mataPelajaran__tahunAjaran=kelas.tahunAjaran
    ).select_related(
        'komponen__mataPelajaran'
    )

    nilai_per_matpel_jenis = defaultdict(lambda: defaultdict(list))

    for nilai in nilai_qs:
        mp = nilai.komponen.mataPelajaran
        jenis = nilai.komponen.tipeKomponen
        key = (mp.id, mp.nama, jenis)
        nilai_per_matpel_jenis[key][nilai.student.id].append(nilai.nilai)

    for (mp_id, mp_nama, jenis), siswa_nilai_dict in nilai_per_matpel_jenis.items():
        total_scores = []
        grade_counts = Counter()

        for nilai_list in siswa_nilai_dict.values():
            if not nilai_list:
                continue
            avg_score = sum(nilai_list) / len(nilai_list)
            grade = get_grade(avg_score)
            grade_counts[grade.lower()] += 1
            total_scores.append(avg_score)

        overall_avg = sum(total_scores) / len(total_scores) if total_scores else 0

        result.append({
            'id_mata_pelajaran': mp_id,
            'mata_pelajaran': mp_nama,
            'jenis': jenis,
            'rata_rata': round(overall_avg, 2),
            'distribusi': dict(grade_counts)
        })

    return result

def get_top_and_risk_students(kelas_id):
    kelas = Kelas.objects.get(id=kelas_id)
    siswa_list = kelas.siswa.select_related('user').all()
    siswa_ids = [siswa.user_id for siswa in siswa_list]

    nilai_qs = (
        Nilai.objects
        .filter(
            student__id__in=siswa_ids,
            komponen__mataPelajaran__tahunAjaran=kelas.tahunAjaran
        )
        .select_related('student', 'komponen', 'komponen__mataPelajaran')
    )

    nilai_per_siswa = defaultdict(lambda: {
        'nama': '',
        'total': 0,
        'count': 0,
        'pengetahuan_total': 0,
        'pengetahuan_count': 0,
        'keterampilan_total': 0,
        'keterampilan_count': 0,
    })

    for nilai in nilai_qs:
        sid = nilai.student.id
        student = Student.objects.get(user_id=sid)
        nama = student.name

        data = nilai_per_siswa[sid]
        data['nama'] = nama
        data['total'] += nilai.nilai
        data['count'] += 1

        if nilai.komponen.tipeKomponen.lower() == 'pengetahuan':
            data['pengetahuan_total'] += nilai.nilai
            data['pengetahuan_count'] += 1
        elif nilai.komponen.tipeKomponen.lower() == 'keterampilan':
            data['keterampilan_total'] += nilai.nilai
            data['keterampilan_count'] += 1

    siswa_stats = []
    for sid, data in nilai_per_siswa.items():
        if data['count'] == 0:
            continue

        rerata = data['total'] / data['count']
        nilai_pengetahuan = data['pengetahuan_total'] / data['pengetahuan_count'] if data['pengetahuan_count'] else 0
        nilai_keterampilan = data['keterampilan_total'] / data['keterampilan_count'] if data['keterampilan_count'] else 0

        siswa_stats.append({
            'id': sid,
            'namaSiswa': data['nama'],
            'rerataNilai': round(rerata, 2),
            'nilaiPengetahuan': round(nilai_pengetahuan, 2),
            'nilaiKeterampilan': round(nilai_keterampilan, 2),
        })

    siswa_terbaik = sorted(siswa_stats, key=lambda x: x['rerataNilai'], reverse=True)[:10]
    siswa_risiko = [s for s in siswa_stats if s['rerataNilai'] < 75]

    return {
        'siswa_terbaik': siswa_terbaik,
        'siswa_risiko_akademik': siswa_risiko
    }