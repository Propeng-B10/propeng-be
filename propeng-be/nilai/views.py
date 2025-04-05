from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Nilai
from .serializers import NilaiSerializer

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

# api/views.py

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt # Hanya untuk testing/API stateless
import json
from decimal import Decimal, InvalidOperation

# Impor model Anda (sesuaikan path jika perlu)
from matapelajaran.models import MataPelajaran
from komponenpenilaian.models import KomponenPenilaian
from user.models import Student, Teacher # Asumsi Student & Teacher ada di app 'user'
from nilai.models import Nilai # Model Nilai yang diberikan
from kelas.models import Kelas # Untuk mendapatkan nama kelas siswa

# Helper function untuk error response
def error_response(message, status=400):
    return JsonResponse({'message': message, 'error': True}, status=status)

# --- View untuk /api/subjects/<matapelajaran_id>/gradedata/ ---
@csrf_exempt # Hapus jika menggunakan autentikasi session/token yang proper
@require_http_methods(["GET", "POST"])
def grade_data_view(request: HttpRequest, matapelajaran_id: int):
    """
    Handles GET and POST requests for grade data of a specific MataPelajaran.
    GET: Returns student list, assessment components, subject name, and initial grades.
    POST: Saves or updates a student's grade for the MataPelajaran.
          NOTE: Due to the provided Nilai model structure, only one grade per
                student per MataPelajaran can be saved, not per component.
    """
    try:
        matapelajaran = MataPelajaran.objects.prefetch_related(
            'siswa_terdaftar', # Prefetch students registered to the subject
            'komponenpenilaian_matpel' # Prefetch assessment components
        ).get(id=matapelajaran_id, isDeleted=False, isActive=True)
    except MataPelajaran.DoesNotExist:
        return error_response(f"Mata Pelajaran dengan ID {matapelajaran_id} tidak ditemukan atau tidak aktif.", status=404)
    except Exception as e:
         print(f"[API Error] Error fetching MataPelajaran: {e}")
         return error_response("Terjadi kesalahan saat mengambil data mata pelajaran.", status=500)

    # --- Handler GET ---
    if request.method == 'GET':
        try:
            # 1. Ambil daftar siswa
            students_queryset = matapelajaran.siswa_terdaftar.filter(isDeleted=False, isActive=True).select_related('kelas') # Ambil data kelas siswa
            students_list = []
            for student_profile in students_queryset:
                # Cari kelas tempat siswa terdaftar
                # Model Student tidak secara langsung link ke Kelas tunggal, tapi Kelas punya M2M ke Student
                # Cara paling mudah adalah mencari kelas yang mengandung siswa ini
                kelas_siswa = Kelas.objects.filter(siswa=student_profile).first() # Ambil kelas pertama yg cocok
                students_list.append({
                    "id": str(student_profile.user_id), # Gunakan ID dari User model
                    "name": student_profile.name or student_profile.user.username,
                    "class": kelas_siswa.namaKelas if kelas_siswa else "N/A" # Ambil nama kelas
                })

            # 2. Ambil komponen penilaian
            assessment_components = list(matapelajaran.komponenpenilaian_matpel.values(
                'id', 'namaKomponen', 'bobotKomponen'
            ))
            # Ubah nama field agar sesuai dengan frontend (jika perlu)
            assessment_components_formatted = [
                {'id': str(comp['id']), 'name': comp['namaKomponen'], 'weight': comp['bobotKomponen']}
                for comp in assessment_components
            ]

            # 3. Siapkan initialGrades
            # !! PERHATIAN !!: Model Nilai yang diberikan hanya menyimpan SATU nilai
            # per siswa per matapelajaran, BUKAN per komponen.
            # Oleh karena itu, kita tidak bisa mengisi initialGrades per komponen secara akurat.
            # Kita akan kembalikan struktur yang diharapkan frontend, tapi isinya null.
            initial_grades = {}
            # Ambil semua nilai yang ada untuk matapelajaran ini
            existing_nilai = Nilai.objects.filter(
                matapelajaran=matapelajaran,
                student_id__in=[s['id'] for s in students_list] # Filter by student user_ids
            ).values('student_id', 'nilai') # Ambil student_id dan nilai

            # Buat mapping student_id -> nilai (nilai tunggal dari model Nilai)
            student_overall_grade_map = {str(n['student_id']): n['nilai'] for n in existing_nilai}

            for student_data in students_list:
                student_id = student_data['id']
                initial_grades[student_id] = {}
                 # Isi semua komponen dengan null karena model tidak mendukung nilai per komponen
                for comp in assessment_components_formatted:
                    initial_grades[student_id][comp['id']] = None # Default ke null
                # Jika Anda ingin menampilkan nilai tunggal dari model Nilai di *setiap* komponen (kurang ideal):
                # overall_grade = student_overall_grade_map.get(student_id)
                # for comp in assessment_components_formatted:
                #     initial_grades[student_id][comp['id']] = float(overall_grade) if overall_grade is not None else None


            # 4. Siapkan data respons
            response_data = {
                "students": students_list,
                "assessmentComponents": assessment_components_formatted,
                "subjectName": matapelajaran.nama,
                "initialGrades": initial_grades
            }
            print(f"[API GET /api/subjects/{matapelajaran_id}/gradedata] Data dikirim.")
            return JsonResponse(response_data, status=200)

        except Exception as e:
            print(f"[API GET /api/subjects/{matapelajaran_id}/gradedata] Error: {e}")
            return error_response("Terjadi kesalahan internal saat memproses data.", status=500)

    # --- Handler POST ---
    elif request.method == 'POST':
        try:
            # 1. Parse body JSON
            try:
                data = json.loads(request.body)
                student_user_id = data.get('studentId')
                component_id = data.get('componentId') # Komponen ID diterima dari frontend
                score_input = data.get('score') # Bisa null, string, atau number
            except json.JSONDecodeError:
                return error_response("Format JSON pada body request tidak valid.", status=400)

            # 2. Validasi input dasar
            if student_user_id is None or component_id is None or score_input is None:
                return error_response("Data tidak lengkap (membutuhkan studentId, componentId, score).", status=400)

            # 3. Konversi dan validasi score
            final_score = None
            if score_input is not None and score_input != '':
                try:
                    numeric_score = Decimal(str(score_input)) # Konversi ke Decimal
                    if not (0 <= numeric_score <= 100):
                        return error_response("Nilai tidak valid. Harus angka antara 0-100 atau kosong/null.", status=400)
                    final_score = numeric_score
                except (ValueError, TypeError, InvalidOperation):
                     return error_response("Format nilai tidak valid. Harus berupa angka.", status=400)

            # 4. Validasi Siswa dan Komponen
            try:
                # Cari student berdasarkan user_id
                student = Student.objects.get(user_id=student_user_id)
                # Cek apakah siswa terdaftar di matapelajaran ini
                if not matapelajaran.siswa_terdaftar.filter(user_id=student_user_id).exists():
                     return error_response(f"Siswa dengan ID {student_user_id} tidak terdaftar di mata pelajaran ini.", status=400)
            except Student.DoesNotExist:
                 return error_response(f"Siswa dengan ID {student_user_id} tidak ditemukan.", status=404)

            try:
                # Cek apakah komponen ada di matapelajaran ini
                 komponen = KomponenPenilaian.objects.get(id=component_id, mataPelajaran=matapelajaran)
            except KomponenPenilaian.DoesNotExist:
                 return error_response(f"Komponen Penilaian dengan ID {component_id} tidak valid untuk mata pelajaran ini.", status=400)

            # 5. Simpan/Update Nilai
            # !! PERHATIAN !!: Karena model Nilai hanya punya satu field `nilai` per siswa
            # per matapelajaran, kita akan mengupdate record Nilai tunggal ini.
            # Informasi `componentId` dari frontend TIDAK dapat digunakan secara efektif
            # untuk menyimpan nilai per komponen dengan model ini.
            # Kode berikut akan membuat atau memperbarui SATU record Nilai untuk siswa dan matpel ini.
            try:
                nilai_obj, created = Nilai.objects.update_or_create(
                    matapelajaran=matapelajaran,
                    student=student, # Gunakan instance Student
                    defaults={'nilai': final_score} # Update nilai
                )
                action = "dibuat" if created else "diperbarui"
                print(f"[API POST /api/subjects/{matapelajaran_id}/gradedata] Nilai {action}: Siswa={student_user_id}, Matpel={matapelajaran_id}, Nilai={final_score}")
                return JsonResponse({
                    "message": f"Nilai berhasil {action} (in-memory) untuk kelas {matapelajaran.nama}.",
                    "studentId": student_user_id,
                    # 'componentId': component_id, # Mungkin tidak relevan dikembalikan jika tidak disimpan per komponen
                    'savedScore': float(final_score) if final_score is not None else None
                }, status=200)

            except Exception as e:
                 print(f"[API POST /api/subjects/{matapelajaran_id}/gradedata] Error saving Nilai: {e}")
                 return error_response("Gagal menyimpan nilai ke database.", status=500)

        except Exception as e:
            print(f"[API POST /api/subjects/{matapelajaran_id}/gradedata] Error: {e}")
            return error_response("Terjadi kesalahan internal saat menyimpan nilai.", status=500)

# --- View untuk /api/guru/mata-pelajaran/ ---
@require_GET
def get_teacher_subjects_summary(request: HttpRequest):
    """
    Returns a summary list of all active MataPelajaran.
    NOTE: Status calculation is based on the provided Nilai model (one grade per student per subject).
    """
    print("[API GET /api/guru/mata-pelajaran] Fetching subject list summary...")
    try:
        # Ambil semua matapelajaran aktif (atau filter berdasarkan guru jika diperlukan nanti)
        active_subjects = MataPelajaran.objects.filter(
            isDeleted=False, isActive=True
        ).prefetch_related(
            'komponenpenilaian_matpel', 'siswa_terdaftar'
        ).select_related('tahunAjaran') # Ambil data tahun ajaran juga

        summary_list = []
        for subject in active_subjects:
            components = subject.komponenpenilaian_matpel.all()
            students = subject.siswa_terdaftar.filter(isActive=True, isDeleted=False) # Filter siswa aktif

            component_count = components.count()
            total_weight = sum(comp.bobotKomponen for comp in components if comp.bobotKomponen is not None)
            student_count = students.count()

            # Hitung Status Pengisian Nilai (berdasarkan model Nilai yang ada)
            status = 'Belum Dimulai'
            if student_count > 0 :
                 # Hitung berapa banyak siswa yang SUDAH punya record Nilai untuk matpel ini
                filled_count = Nilai.objects.filter(
                    matapelajaran=subject,
                    student__in=students # Cek dari siswa yang terdaftar & aktif
                ).count()

                # Jika semua siswa punya record Nilai (meskipun hanya 1 nilai per siswa)
                if filled_count == student_count:
                    status = 'Terisi Penuh'
                elif filled_count > 0:
                    status = 'Dalam Proses'
                # else: status = 'Belum Dimulai' # Default

            # Format komponen untuk dimasukkan ke summary
            components_data = [
                 {'id': str(comp.id), 'name': comp.namaKomponen, 'weight': comp.bobotKomponen}
                 for comp in components
            ]

            summary_list.append({
                "id": str(subject.id), # ID primary key
                "subjectId": subject.kode, # Gunakan kode sebagai subjectId? Atau tetap ID?
                "name": subject.nama,
                "academicYear": str(subject.tahunAjaran.tahunAjaran) if subject.tahunAjaran else "N/A",
                "totalWeight": total_weight,
                "componentCount": component_count,
                "studentCount": student_count,
                "status": status,
                "components": components_data # Sertakan detail komponen
            })

        print(f"[API GET /api/guru/mata-pelajaran] Summary generated: {len(summary_list)} subjects.")
        return JsonResponse(summary_list, status=200, safe=False) # safe=False karena return berupa list

    except Exception as e:
        print(f"[API GET /api/guru/mata-pelajaran] Error: {e}")
        return error_response("Kesalahan Server Internal saat mengambil summary.", status=500)