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
from komponenpenilaian.models import KomponenPenilaian, PENGETAHUAN, KETERAMPILAN
from collections import defaultdict # Untuk memudahkan pengelompokan

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
@permission_classes([IsAuthenticated])
def grade_data_view(request: Request, matapelajaran_id: int):
    """
    Handles GET/POST for grade data.
    GET: Returns students, all components (with type), and a single initialGrades dict.
    POST: Saves/Updates grade for a specific student and component (type is inherent in component).
    """
    # --- Dapatkan profil Guru & MataPelajaran, Cek Permission (SAMA) ---
    try: requesting_teacher = request.user.teacher
    except (Teacher.DoesNotExist, AttributeError): return drf_error_response("Akses ditolak.", status.HTTP_403_FORBIDDEN)
    try:
        # Prefetch komponen penilaian
        matapelajaran = MataPelajaran.objects.select_related('teacher__user', 'tahunAjaran').prefetch_related(
            'siswa_terdaftar__user', # Include user relation for student
            'komponenpenilaian_matpel' # Prefetch components
        ).get(id=matapelajaran_id, isDeleted=False, isActive=True)
    except MataPelajaran.DoesNotExist: return drf_error_response(f"MatPel tidak ditemukan.", status.HTTP_404_NOT_FOUND)
    if matapelajaran.teacher and matapelajaran.teacher != requesting_teacher: return drf_error_response("Tidak ada izin.", status.HTTP_403_FORBIDDEN)

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


# --- View get_teacher_subjects_summary (SETELAH PERUBAHAN) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_subjects_summary(request: Request):
    # ... (Logika get teacher SAMA) ...
    try: logged_in_teacher = request.user.teacher
    except (Teacher.DoesNotExist, AttributeError): return drf_error_response("Akses guru ditolak.", status.HTTP_403_FORBIDDEN)

    print(f"[API GET /api/nilai/subjects/] Fetching summary for teacher: {logged_in_teacher.user.username}")
    try:
        active_subjects = MataPelajaran.objects.filter(
            teacher=logged_in_teacher, isDeleted=False, isActive=True
        ).prefetch_related(
            'komponenpenilaian_matpel',
            'siswa_terdaftar__user' # Prefetch user siswa juga
        ).select_related('tahunAjaran', 'teacher__user') # Prefetch user guru

        summary_list = []
        for subject in active_subjects:
            components = subject.komponenpenilaian_matpel.all()
            students_qs = subject.siswa_terdaftar.filter(isActive=True, isDeleted=False)

            component_count = components.count()
            total_weight = sum(comp.bobotKomponen for comp in components if comp.bobotKomponen is not None)
            student_count = students_qs.count()

            subject_status = 'Belum Dimulai' # Status Awal

            # Perhitungan Status (SUDAH DISESUAIKAN)
            # Total entri = jumlah siswa * jumlah komponen (TIDAK PERLU * 2)
            total_possible_entries = student_count * component_count # <--- PERUBAHAN DI SINI

            if total_possible_entries > 0 :
                student_user_ids = [s.user_id for s in students_qs if s.user_id]
                component_ids = components.values_list('id', flat=True)

                if student_user_ids and list(component_ids): # Pastikan ada ID siswa dan komponen
                    # Hitung jumlah record Nilai yang sudah ada
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
                # else: Jika tidak ada siswa atau komponen, status tetap 'Belum Dimulai'

            # Sertakan tipe komponen dalam data komponen jika diperlukan di frontend summary
            components_data = [{
                'id': str(comp.id),
                'name': comp.namaKomponen,
                'weight': comp.bobotKomponen,
                'type': comp.tipeKomponen # Bisa ditambahkan jika perlu
             } for comp in components]

            summary_list.append({
                "id": str(subject.id),
                "subjectId": subject.kode,
                "name": subject.nama,
                "academicYear": str(subject.tahunAjaran.tahunAjaran) if subject.tahunAjaran else "N/A",
                "totalWeight": total_weight,
                "componentCount": component_count,
                "studentCount": student_count,
                "status": subject_status, # <-- Status yang sudah dihitung ulang
                "components": components_data # <-- Data komponen
            })

        return Response(summary_list, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[API GET /api/nilai/subjects/] Error for teacher {logged_in_teacher.user.username}: {e}")
        traceback.print_exc()
        return drf_error_response("Kesalahan Server Internal saat mengambil summary.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


        # 3. Ambil Semua Nilai Siswa untuk Mata Pelajaran di Kelas Aktif
        # Filter Nilai berdasarkan student dan komponen yang mata pelajarannya
        # sesuai dengan tahun ajaran & angkatan kelas aktif siswa
        # serta siswa terdaftar di matpel tsb.
        nilai_list = Nilai.objects.filter(
            student=user,
            komponen__mataPelajaran__tahunAjaran=kelas_aktif.tahunAjaran,
            # Optional: Filter berdasarkan angkatan jika relevan dan ada di MataPelajaran
            # komponen__mataPelajaran__angkatan=kelas_aktif.angkatan,
            komponen__mataPelajaran__siswa_terdaftar=student_profile, # Pastikan siswa terdaftar di matpel
            komponen__mataPelajaran__isActive=True, # Hanya dari matpel aktif
            komponen__mataPelajaran__isDeleted=False
        ).select_related(
            'komponen__mataPelajaran', # Untuk dapat nama & kategori matpel
            'komponen' # Untuk dapat nama & tipe komponen
        ).order_by(
            'komponen__mataPelajaran__nama', # Urutkan berdasarkan nama matpel
            'komponen__tipeKomponen',       # Lalu berdasarkan tipe komponen
            'komponen__namaKomponen'        # Lalu nama komponen
        )

        # 4. Strukturisasi Data Hasil
        # Gunakan defaultdict untuk memudahkan pengelompokan
        nilai_per_matpel = defaultdict(lambda: {
            'id': None,
            'nama': None,
            'kategori': None,
            'kode': None,
            'pengetahuan': [],
            'keterampilan': []
        })

        for nilai_record in nilai_list:
            komponen = nilai_record.komponen
            matpel = komponen.mataPelajaran
            matpel_id_str = str(matpel.id) # Gunakan ID sebagai key unik

            # Isi detail matpel jika belum ada
            if nilai_per_matpel[matpel_id_str]['id'] is None:
                nilai_per_matpel[matpel_id_str]['id'] = matpel_id_str
                nilai_per_matpel[matpel_id_str]['nama'] = matpel.nama
                nilai_per_matpel[matpel_id_str]['kategori'] = matpel.get_kategoriMatpel_display() # Dapatkan display name
                nilai_per_matpel[matpel_id_str]['kode'] = matpel.kode

            # Siapkan data entri nilai
            grade_entry = {
                'komponen': komponen.namaKomponen,
                'bobot': komponen.bobotKomponen, # Mungkin berguna untuk info
                'nilai': float(nilai_record.nilai) if nilai_record.nilai is not None else None
            }

            # Masukkan ke list yang sesuai (Pengetahuan/Keterampilan)
            if komponen.tipeKomponen == PENGETAHUAN:
                nilai_per_matpel[matpel_id_str]['pengetahuan'].append(grade_entry)
            elif komponen.tipeKomponen == KETERAMPILAN:
                nilai_per_matpel[matpel_id_str]['keterampilan'].append(grade_entry)

        # 5. Konversi hasil ke format list (lebih umum untuk API)
        final_result = list(nilai_per_matpel.values())

        # Data tambahan (opsional)
        response_data = {
            "kelas": {
                "nama": kelas_aktif.namaKelas,
                "tahun_ajaran": str(kelas_aktif.tahunAjaran),
                "angkatan": kelas_aktif.angkatan
            },
            "nilai_siswa": final_result
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error fetching student grades: {e}")
        traceback.print_exc()
        return drf_error_response("Terjadi kesalahan internal saat mengambil data nilai.", status.HTTP_500_INTERNAL_SERVER_ERROR)
