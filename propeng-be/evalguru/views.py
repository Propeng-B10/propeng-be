from django.http import JsonResponse
from evalguru.models import *
from matapelajaran.models import MataPelajaran
from user.models import Teacher, Student
from kelas.models import Kelas 
from tahunajaran.models import TahunAjaran 
from django.db.models import Avg, F, Count, Subquery, OuterRef, IntegerField
from collections import defaultdict
from rest_framework.decorators import api_view
from django.db import transaction
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from user.views import IsStudentRole, IsTeacherRole


def get_student_main_class_info(student_obj):
    if not student_obj:
        return "N/A", "N/A"
    
    kelas_queryset = Kelas.objects.filter(siswa=student_obj).select_related('tahunAjaran').order_by('-tahunAjaran__tahunAjaran', 'namaKelas')
    kelas_obj = kelas_queryset.first()

    if kelas_obj:
        nama_kelas_str = kelas_obj.namaKelas if hasattr(kelas_obj, 'namaKelas') else "N/A"
        tahun_ajaran_str = "N/A"
        if hasattr(kelas_obj, 'tahunAjaran') and kelas_obj.tahunAjaran:
            tahun_ajaran_str = str(kelas_obj.tahunAjaran.tahunAjaran) if hasattr(kelas_obj.tahunAjaran, 'tahunAjaran') else "N/A"
        return nama_kelas_str, tahun_ajaran_str
    return "N/A", "N/A"

@api_view(['POST'])
def siswafill_evalguru(request):
    main_data = request.data 

    evaluasi_skor_list = main_data.get('evaluasi_skor') 
    kritik_saran_keseluruhan = main_data.get('kritik_saran_keseluruhan', None) 

    if not isinstance(evaluasi_skor_list, list):
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Kunci 'evaluasi_skor' harus berisi list (array) data evaluasi.","errors": "Format data tidak valid."}, status=status.HTTP_400_BAD_REQUEST)

    if not evaluasi_skor_list:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "List 'evaluasi_skor' tidak boleh kosong.","errors": "Data evaluasi skor diperlukan."}, status=status.HTTP_400_BAD_REQUEST)

    created_evaluations_details = []
    errors = []
    
    first_item_for_context = evaluasi_skor_list[0]
    common_siswa_id = first_item_for_context.get('siswa_id')
    common_guru_id = first_item_for_context.get('guru_id')
    common_matapelajaran_id = first_item_for_context.get('matapelajaran_id')

    if not all([common_siswa_id, common_guru_id, common_matapelajaran_id]):
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "siswa_id, guru_id, dan matapelajaran_id wajib ada di setiap item evaluasi skor dan harus konsisten untuk satu pengisian form.", "errors": "Konteks evaluasi tidak jelas."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        siswa_obj = Student.objects.get(pk=common_siswa_id)
        guru_obj = Teacher.objects.get(pk=common_guru_id)
        matapelajaran_obj_ref = MataPelajaran.objects.get(pk=common_matapelajaran_id)

        with transaction.atomic():
            for index, eval_data_item in enumerate(evaluasi_skor_list):
                if not (eval_data_item.get('siswa_id') == common_siswa_id and \
                        eval_data_item.get('guru_id') == common_guru_id and \
                        eval_data_item.get('matapelajaran_id') == common_matapelajaran_id):
                    errors.append({"index": index, "item_data": eval_data_item, "error": "Kombinasi siswa_id, guru_id, matapelajaran_id pada item ini berbeda dari konteks utama form."})
                    continue

                indikator = eval_data_item.get('indikator')
                variabel = eval_data_item.get('variabel')
                skorlikert = eval_data_item.get('skorlikert')

                if not all([indikator, variabel, skorlikert]): 
                    errors.append({"index": index, "item_data": eval_data_item, "error": "Data tidak lengkap (indikator, variabel, skorlikert wajib diisi)."})
                    continue
                
                try: 
                    evaluasi_guru = EvalGuru.objects.create(
                        siswa_id=common_siswa_id, 
                        guru_id=common_guru_id, 
                        matapelajaran_id=common_matapelajaran_id,
                        indikator=indikator, 
                        variabel=variabel, 
                        skorlikert=skorlikert,
                        kritik_saran=kritik_saran_keseluruhan
                    )
                    
                    nama_siswa = siswa_obj.name if hasattr(siswa_obj, 'name') else "N/A"
                    nama_guru = guru_obj.name if hasattr(guru_obj, 'name') else "N/A"
                    nama_matapelajaran = matapelajaran_obj_ref.nama if hasattr(matapelajaran_obj_ref, 'nama') else "N/A"
                    
                    kelas_siswa_str, tahun_ajaran_siswa_str = get_student_main_class_info(siswa_obj)
                    
                    tahun_ajaran_mapel_str = "N/A"
                    if hasattr(matapelajaran_obj_ref, 'tahunAjaran') and matapelajaran_obj_ref.tahunAjaran:
                        tahun_ajaran_mapel_str = str(matapelajaran_obj_ref.tahunAjaran.tahunAjaran) if hasattr(matapelajaran_obj_ref.tahunAjaran, 'tahunAjaran') else "N/A"

                    created_evaluations_details.append({
                        "id": evaluasi_guru.id,
                        "siswa_id": evaluasi_guru.siswa_id, "siswa_nama": nama_siswa,
                        "guru_id": evaluasi_guru.guru_id, "guru_nama": nama_guru,
                        "matapelajaran_id": evaluasi_guru.matapelajaran_id, "matapelajaran_nama": nama_matapelajaran,
                        "info_kelas_siswa": kelas_siswa_str,
                        "info_tahun_ajaran_siswa": tahun_ajaran_siswa_str,
                        "info_tahun_ajaran_mapel": tahun_ajaran_mapel_str,
                        "indikator": evaluasi_guru.indikator, 
                        "variabel": evaluasi_guru.variabel, 
                        "skorlikert": evaluasi_guru.skorlikert,
                        "kritik_saran_tersimpan": evaluasi_guru.kritik_saran 
                    })
                except Exception as e:
                    errors.append({"index": index, "item_data": eval_data_item, "error": f"Gagal membuat item evaluasi: {str(e)}"})
            
            if errors: 
                raise Exception("Terjadi error pada beberapa item, transaksi dibatalkan.")

    except Student.DoesNotExist: 
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": f"Siswa dengan id {common_siswa_id} tidak ditemukan untuk konteks utama form."}, status=status.HTTP_400_BAD_REQUEST)
    except Teacher.DoesNotExist: 
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": f"Guru dengan id {common_guru_id} tidak ditemukan untuk konteks utama form."}, status=status.HTTP_400_BAD_REQUEST)
    except MataPelajaran.DoesNotExist: 
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": f"Mata Pelajaran id {common_matapelajaran_id} tidak ditemukan untuk konteks utama form."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e: 

        final_errors = errors if errors else [{"error_transaksi": str(e)}]
        return JsonResponse({
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR, 
            "message": "Gagal memproses evaluasi karena terjadi kesalahan.", 
            "failed_items_details": final_errors
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({
        "status": status.HTTP_201_CREATED, 
        "message": "Semua item evaluasi dan kritik saran berhasil diisi.", 
        "data": created_evaluations_details,
        "kritik_saran_keseluruhan_tersimpan": kritik_saran_keseluruhan 
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def guru_get_evalguru_in_mapel(request):
    guru_id_str = request.query_params.get('guru_id')
    matapelajaran_id_str = request.query_params.get('matapelajaran_id')

    if not guru_id_str or not matapelajaran_id_str: 
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "guru_id dan matapelajaran_id diperlukan."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        guru_id = int(guru_id_str)
        matapelajaran_id = int(matapelajaran_id_str)
    except ValueError: 
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "ID harus angka."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        matapelajaran_obj = MataPelajaran.objects.get(id=matapelajaran_id)
        nama_matapelajaran = matapelajaran_obj.nama if hasattr(matapelajaran_obj, 'nama') else "N/A"
        tahun_ajaran_mapel_str = "N/A"
        if hasattr(matapelajaran_obj, 'tahunAjaran') and matapelajaran_obj.tahunAjaran:
            tahun_ajaran_mapel_str = str(matapelajaran_obj.tahunAjaran.tahunAjaran) if hasattr(matapelajaran_obj.tahunAjaran, 'tahunAjaran') else "N/A"
    except MataPelajaran.DoesNotExist: 
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Mata Pelajaran tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

    evaluations_for_mapel_query = EvalGuru.objects.filter(
        guru_id=guru_id, 
        matapelajaran_id=matapelajaran_id
    ).select_related('siswa') 

    unique_kelas_names = set()
    all_kritik_saran = [] 
    
    kritik_saran_per_siswa = defaultdict(set)
    for ev_entry in evaluations_for_mapel_query:
        kelas_siswa_str, _ = get_student_main_class_info(ev_entry.siswa)
        if kelas_siswa_str != "N/A":
            unique_kelas_names.add(kelas_siswa_str)
        
        if ev_entry.kritik_saran: 
            kritik_saran_per_siswa[ev_entry.siswa_id].add(ev_entry.kritik_saran)

    for siswa_id, saran_set in kritik_saran_per_siswa.items():
        all_kritik_saran.extend(list(saran_set))

    kelas_display_str = ", ".join(sorted(list(unique_kelas_names))) if unique_kelas_names else "N/A"

    evaluasi_aggregat = evaluations_for_mapel_query.values('variabel', 'indikator')\
                                        .annotate(avg_skor=Avg('skorlikert'))\
                                        .order_by('variabel', 'indikator')
    skor_map = {(item['variabel'], item['indikator']): item['avg_skor'] for item in evaluasi_aggregat}
    hasil_evaluasi_list = []
    for variabel_choice in EvalGuru.pilihanvariabel:
        var_id = variabel_choice[0] 
        data_per_variabel = {"variabel_id": var_id}
        for indikator_choice in EvalGuru.pilihanindikator:
            indicator_id = indikator_choice[0]
            rata_rata = skor_map.get((var_id, indicator_id))
            data_per_variabel[f"Indikator {indicator_id}"] = f"{rata_rata:.2f} / 5.00" if rata_rata is not None else "- / 5.00"
        hasil_evaluasi_list.append(data_per_variabel)

    return JsonResponse({
        "status": status.HTTP_200_OK, 
        "message": "Berhasil mendapatkan data evaluasi guru",
        "nama_matapelajaran": nama_matapelajaran,
        "tahun_ajaran_mapel": tahun_ajaran_mapel_str,
        "daftar_kelas_evaluasi": kelas_display_str, 
        "daftar_kritik_saran": all_kritik_saran if all_kritik_saran else ["Tidak ada kritik/saran yang diberikan."],
        "hasil_evaluasi": hasil_evaluasi_list,
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def guru_get_all_evaluations_summary(request):
    guru_id_str = request.query_params.get('guru_id')
    if not guru_id_str: return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "guru_id diperlukan."}, status=status.HTTP_400_BAD_REQUEST)
    try: guru_id = int(guru_id_str)
    except ValueError: return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "guru_id harus angka."}, status=status.HTTP_400_BAD_REQUEST)

    evaluations_for_guru = EvalGuru.objects.filter(guru_id=guru_id)\
                                        .select_related('matapelajaran', 'matapelajaran__tahunAjaran', 'siswa')\
                                        .order_by('matapelajaran_id')
    
    if not evaluations_for_guru.exists(): return JsonResponse({"status": status.HTTP_200_OK, "message": "Tidak ada data evaluasi untuk guru ini.", "data_evaluasi": []}, status=status.HTTP_200_OK)

    mapel_eval_data = defaultdict(lambda: {
        'matapelajaran_obj': None, 
        'kelas_info_siswa': set(), 
        'tahun_ajaran_mapel_str': "N/A",
        'skor_collections': defaultdict(list)
    })

    for ev in evaluations_for_guru:
        mapel_id = ev.matapelajaran_id
        current_mapel_data = mapel_eval_data[mapel_id]
        if current_mapel_data['matapelajaran_obj'] is None: 
            current_mapel_data['matapelajaran_obj'] = ev.matapelajaran
            if hasattr(ev.matapelajaran, 'tahunAjaran') and ev.matapelajaran.tahunAjaran:
                current_mapel_data['tahun_ajaran_mapel_str'] = str(ev.matapelajaran.tahunAjaran.tahunAjaran) if hasattr(ev.matapelajaran.tahunAjaran, 'tahunAjaran') else "N/A"

        kelas_siswa_str, _ = get_student_main_class_info(ev.siswa)
        if kelas_siswa_str != "N/A":
            current_mapel_data['kelas_info_siswa'].add(kelas_siswa_str)
        
        current_mapel_data['skor_collections'][ev.variabel].append(ev.skorlikert)

    all_mapel_summary_data = []
    for mapel_id, data in mapel_eval_data.items():
        mapel_obj = data['matapelajaran_obj']
        
        kelas_display_str = ", ".join(sorted(list(data['kelas_info_siswa']))) if data['kelas_info_siswa'] else "N/A"
        
        mapel_summary = {
            "matapelajaran_id": mapel_obj.id,
            "nama_matapelajaran": mapel_obj.nama if hasattr(mapel_obj, 'nama') else "N/A",
            "tahun_ajaran_mapel": data['tahun_ajaran_mapel_str'],
            "daftar_kelas_evaluasi": kelas_display_str,
            "skor_per_variabel": {}
        }
        for variabel_choice in EvalGuru.pilihanvariabel:
            var_id = variabel_choice[0]  
            skor_list = data['skor_collections'].get(var_id, [])
            avg_skor_value = sum(skor_list) / len(skor_list) if skor_list else None
            mapel_summary["skor_per_variabel"][str(var_id)] = f"{avg_skor_value:.2f} / 5.00" if avg_skor_value is not None else "- / 5.00"
        all_mapel_summary_data.append(mapel_summary)

    return JsonResponse({"status": status.HTTP_200_OK, "message": "Rangkuman evaluasi per mata pelajaran guru.", "data_evaluasi": all_mapel_summary_data}, status=status.HTTP_200_OK)


@api_view(['GET'])
# @permission_classes([IsAuthenticated]) # Sesuaikan permission jika perlu
def get_overall_teacher_evaluations_overview(request):
    # Menggunakan isianEvalGuru sebagai basis data
    evaluations_base_qs = isianEvalGuru.objects.select_related(
        'guru',
        'matapelajaran',
        'matapelajaran__tahunAjaran'
    ).annotate(
        tahun_ajaran_mapel_val=F('matapelajaran__tahunAjaran__tahunAjaran'),
        nisp_guru_val=F('guru__nisp') 
    ).order_by('tahun_ajaran_mapel_val', 'guru__name')

    if not evaluations_base_qs.exists():
        return JsonResponse({
            "status": status.HTTP_200_OK,
            "message": "Tidak ada data evaluasi.",
            "data_evaluasi_per_tahun": {}
        }, status=status.HTTP_200_OK)

    teacher_scores_by_ta = defaultdict(lambda: defaultdict(lambda: {
        'guru_id': None, 'nama_guru': None, 'nisp': None,
        'scores_per_variable': defaultdict(list), # Skor akan dikumpulkan di sini
        'unique_form_submissions': set() # Untuk menghitung jumlah pengisi unik per guru per TA
    }))

    # Iterasi melalui setiap entri isianEvalGuru
    for form_isian in evaluations_base_qs:
        ta_val = form_isian.tahun_ajaran_mapel_val
        ta_key = str(ta_val) if ta_val is not None else "TA Tidak Diketahui"
        gid = form_isian.guru_id

        teacher_data = teacher_scores_by_ta[ta_key][gid]
        if teacher_data['guru_id'] is None:
            teacher_data['guru_id'] = gid
            teacher_data['nama_guru'] = form_isian.guru.name if hasattr(form_isian.guru, 'name') else "N/A"
            teacher_data['nisp'] = form_isian.nisp_guru_val
        
        # Tambahkan ID siswa dan mapel untuk menghitung pengisi unik per guru
        teacher_data['unique_form_submissions'].add((form_isian.siswa_id, form_isian.matapelajaran_id))

        # Ekstrak skor dari field 'isian' JSON
        if isinstance(form_isian.isian, dict):
            for var_id_str, indicators_data in form_isian.isian.items():
                try:
                    var_id_int = int(var_id_str) # Konversi var_id ke int
                    if isinstance(indicators_data, dict):
                        for _ind_id_str, skor_likert in indicators_data.items():
                            if skor_likert is not None and isinstance(skor_likert, (int, float)):
                                teacher_data['scores_per_variable'][var_id_int].append(int(skor_likert))
                except ValueError:
                    # Abaikan jika var_id_str bukan integer yang valid
                    continue
    
    final_response_data = defaultdict(list)
    for ta_key, guru_data_map in teacher_scores_by_ta.items():
        for guru_id_val, teacher_info in guru_data_map.items():
            ta_filter_int = None
            is_ta_unknown = (ta_key == "TA Tidak Diketahui")
            if not is_ta_unknown:
                try:
                    ta_filter_int = int(ta_key)
                except ValueError:
                    continue 

            # Subquery untuk menghitung jumlah pengisi unik (siswa) per mata pelajaran
            # Menggunakan isianEvalGuru
            pengisi_subquery = isianEvalGuru.objects.filter(
                matapelajaran_id=OuterRef('pk'), 
                guru_id=guru_id_val              
            ).values('matapelajaran_id').annotate(
                c=Count('siswa_id', distinct=True) 
            ).values('c')

            subjects_taught_qs = MataPelajaran.objects.none()
            if ta_filter_int is not None:
                subjects_taught_qs = MataPelajaran.objects.filter(
                    teacher_id=guru_id_val, 
                    tahunAjaran__tahunAjaran=ta_filter_int
                )
            elif is_ta_unknown:
                 subjects_taught_qs = MataPelajaran.objects.filter(
                    teacher_id=guru_id_val,
                    tahunAjaran__isnull=True 
                )
            
            subjects_with_counts = subjects_taught_qs.select_related('tahunAjaran').annotate(
                num_siswa_terdaftar=Count('siswa_terdaftar', distinct=True), # Asumsi relasi many-to-many 'siswa_terdaftar' di MataPelajaran
                num_pengisi_eval=Subquery(pengisi_subquery[:1], output_field=IntegerField()) 
            ).order_by('nama') 

            detail_per_mata_pelajaran_list = []
            mata_pelajaran_summary_names_list = []

            for subject in subjects_with_counts:
                pengisi_count = subject.num_pengisi_eval if subject.num_pengisi_eval is not None else 0
                subject_display_name = subject.nama
                
                mata_pelajaran_summary_names_list.append(subject_display_name)
                
                detail_per_mata_pelajaran_list.append({
                    "matapelajaran_id": subject.id,
                    "nama_matapelajaran": subject_display_name, 
                    "total_pengisi_evaluasi": f"{pengisi_count}",
                    "total_siswa_mapel": f"{subject.num_siswa_terdaftar}",
                })
            
            skor_per_variabel_guru = {}
            # Menggunakan EvalGuru.pilihanvariabel untuk struktur
            if hasattr(EvalGuru, 'pilihanvariabel'):
                for var_choice in EvalGuru.pilihanvariabel:
                    var_id_int = var_choice[0] # Ini sudah integer
                    var_id_str = str(var_id_int) # Untuk key output JSON
                    skor_list = teacher_info['scores_per_variable'].get(var_id_int, []) # Gunakan int key
                    avg_skor = sum(skor_list) / len(skor_list) if skor_list else None
                    skor_per_variabel_guru[var_id_str] = f"{avg_skor:.2f} / 5.00" if avg_skor is not None else "- / 5.00"

            final_response_data[ta_key].append({
                "guru_id": teacher_info['guru_id'],
                "nama_guru": teacher_info['nama_guru'],
                "nisp": teacher_info['nisp'],
                "mata_pelajaran_summary": sorted(list(set(mata_pelajaran_summary_names_list))),
                "detail_per_mata_pelajaran": detail_per_mata_pelajaran_list, 
                "skor_per_variabel": skor_per_variabel_guru 
            })
            
    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Data evaluasi keseluruhan guru per tahun ajaran.", 
        "data_evaluasi_per_tahun": final_response_data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
def get_teacher_evaluation_detail_page(request):
    guru_id_str = request.query_params.get('guru_id')
    tahun_ajaran_val_str = request.query_params.get('tahun_ajaran_id')

    if not guru_id_str or not tahun_ajaran_val_str:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Parameter guru_id dan tahun_ajaran_id (nilai tahun) diperlukan."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guru_id = int(guru_id_str)
        tahun_ajaran_value = int(tahun_ajaran_val_str)
    except ValueError:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "ID guru dan nilai tahun ajaran harus berupa angka."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guru_obj = Teacher.objects.get(pk=guru_id)
        if not TahunAjaran.objects.filter(tahunAjaran=tahun_ajaran_value).exists():
            raise TahunAjaran.DoesNotExist
    except Teacher.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": f"Guru id {guru_id} tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    except TahunAjaran.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": f"Tahun Ajaran dengan nilai '{tahun_ajaran_value}' tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

    info_konteks = {
        "guru_id": guru_obj.user_id if hasattr(guru_obj, 'user_id') else guru_obj.pk,
        "nama_guru": guru_obj.name if hasattr(guru_obj, 'name') else "N/A",
        "nisp": guru_obj.nisp if hasattr(guru_obj, 'nisp') else "N/A",
        "tahun_ajaran": str(tahun_ajaran_value),
        "daftar_matapelajaran_diajar": ["Tidak ada mata pelajaran dengan evaluasi untuk tahun ini."],
        "skor_rata_rata_keseluruhan_guru": "- / 5.00",
        "jumlah_form_evaluasi_terisi_keseluruhan": 0,
    }

    evaluasi_keseluruhan_rerata = {
        "jumlah_form_evaluasi_terisi": 0,
        "total_siswa_diajar_di_matapelajaran_terevaluasi": 0,
        "daftar_kelas_evaluasi_unik_gabungan": "N/A",
        "ringkasan_skor_rata_rata_per_variabel_gabungan": {},
        "detail_skor_rata_rata_per_indikator_gabungan": [],
        "daftar_kritik_saran_gabungan": ["Tidak ada kritik/saran secara keseluruhan."],
        "skor_grand_total_dari_variabel_gabungan": "- / 5.00"
    }
    if hasattr(EvalGuru, 'pilihanvariabel'):
        for var_choice in EvalGuru.pilihanvariabel:
            evaluasi_keseluruhan_rerata["ringkasan_skor_rata_rata_per_variabel_gabungan"][str(var_choice[0])] = "- / 5.00"

    evaluations_in_scope_qs = isianEvalGuru.objects.filter(
        guru_id=guru_id,
        matapelajaran__tahunAjaran__tahunAjaran=tahun_ajaran_value
    ).select_related('matapelajaran', 'siswa', 'guru', 'matapelajaran__tahunAjaran')

    if not evaluations_in_scope_qs.exists():
        return JsonResponse({
            "status": status.HTTP_200_OK,
            "message": f"Tidak ada evaluasi ditemukan untuk guru {info_konteks['nama_guru']} pada tahun ajaran {tahun_ajaran_value}.",
            "info_konteks": info_konteks,
            "evaluasi_per_matapelajaran": [],
            "evaluasi_keseluruhan_rerata": evaluasi_keseluruhan_rerata
        }, status=status.HTTP_200_OK)

    all_likert_scores_overall = []
    overall_scores_by_variable = defaultdict(list)
    overall_scores_by_indicator = defaultdict(lambda: defaultdict(list))
    overall_form_submissions_identifiers = set()
    overall_kritik_saran_set = set()
    overall_unique_kelas_names_set = set()
    mapel_data_aggregator = defaultdict(lambda: {
        'matapelajaran_obj': None,
        'parsed_isian_forms': [],
        'kritik_saran_list_mapel': [],
        'unique_kelas_names_mapel': set(),
        'unique_siswa_ids_mapel': set()
    })
    evaluated_matapelajaran_ids = set()

    for form_isian in evaluations_in_scope_qs:
        if form_isian.matapelajaran:
             evaluated_matapelajaran_ids.add(form_isian.matapelajaran_id)
        if form_isian.siswa and form_isian.matapelajaran:
            overall_form_submissions_identifiers.add((form_isian.siswa_id, form_isian.matapelajaran_id))
        if form_isian.kritik_saran and form_isian.kritik_saran.strip():
            overall_kritik_saran_set.add(form_isian.kritik_saran.strip())
        if form_isian.siswa:
            kelas_siswa_str, _ = get_student_main_class_info(form_isian.siswa)
            if kelas_siswa_str != "N/A":
                overall_unique_kelas_names_set.add(kelas_siswa_str)
                if form_isian.matapelajaran:
                    mapel_data_aggregator[form_isian.matapelajaran_id]['unique_kelas_names_mapel'].add(kelas_siswa_str)

        if isinstance(form_isian.isian, dict):
            for var_id_str, indicators_data in form_isian.isian.items():
                if isinstance(indicators_data, dict):
                    for ind_id_str, skor_likert in indicators_data.items():
                        if isinstance(skor_likert, (int, float)) and 1 <= skor_likert <= 5 :
                            skor_val = int(skor_likert)
                            all_likert_scores_overall.append(skor_val)
                            overall_scores_by_variable[var_id_str].append(skor_val)
                            overall_scores_by_indicator[var_id_str][ind_id_str].append(skor_val)
        
        if form_isian.matapelajaran:
            mapel_id = form_isian.matapelajaran_id
            if mapel_data_aggregator[mapel_id]['matapelajaran_obj'] is None:
                mapel_data_aggregator[mapel_id]['matapelajaran_obj'] = form_isian.matapelajaran
            mapel_data_aggregator[mapel_id]['parsed_isian_forms'].append(form_isian.isian)
            if form_isian.siswa:
                mapel_data_aggregator[mapel_id]['unique_siswa_ids_mapel'].add(form_isian.siswa_id)
            if form_isian.kritik_saran and form_isian.kritik_saran.strip():
                mapel_data_aggregator[mapel_id]['kritik_saran_list_mapel'].append(form_isian.kritik_saran.strip())

    if evaluated_matapelajaran_ids:
        subject_names_taught_list = sorted(list(
            MataPelajaran.objects.filter(pk__in=list(evaluated_matapelajaran_ids)).values_list('nama', flat=True).distinct()
        ))
        if subject_names_taught_list:
            info_konteks["daftar_matapelajaran_diajar"] = subject_names_taught_list
    if all_likert_scores_overall:
        avg_overall_score_konteks = sum(all_likert_scores_overall) / len(all_likert_scores_overall)
        info_konteks["skor_rata_rata_keseluruhan_guru"] = f"{avg_overall_score_konteks:.2f} / 5.00"
    info_konteks["jumlah_form_evaluasi_terisi_keseluruhan"] = len(overall_form_submissions_identifiers)

    evaluasi_keseluruhan_rerata["jumlah_form_evaluasi_terisi"] = len(overall_form_submissions_identifiers)
    total_siswa_diajar_mapel_terevaluasi = 0
    if evaluated_matapelajaran_ids:
        subjects_with_evals_qs = MataPelajaran.objects.filter(
            pk__in=list(evaluated_matapelajaran_ids)
        ).annotate(num_students=Count('siswa_terdaftar', distinct=True))
        for subject in subjects_with_evals_qs:
            total_siswa_diajar_mapel_terevaluasi += subject.num_students
    evaluasi_keseluruhan_rerata["total_siswa_diajar_di_matapelajaran_terevaluasi"] = total_siswa_diajar_mapel_terevaluasi
    if overall_unique_kelas_names_set:
        evaluasi_keseluruhan_rerata["daftar_kelas_evaluasi_unik_gabungan"] = ", ".join(sorted(list(overall_unique_kelas_names_set)))

    temp_ringkasan_skor_var_gabungan = {}
    valid_overall_variable_scores_float = []
    if hasattr(EvalGuru, 'pilihanvariabel'):
        for var_choice in EvalGuru.pilihanvariabel:
            var_id_int = var_choice[0]
            var_id_str = str(var_id_int)
            skor_list = overall_scores_by_variable.get(var_id_str, [])
            avg_skor_str = "- / 5.00"
            if skor_list:
                avg_skor = sum(skor_list) / len(skor_list)
                avg_skor_str = f"{avg_skor:.2f} / 5.00"
                valid_overall_variable_scores_float.append(avg_skor)
            temp_ringkasan_skor_var_gabungan[var_id_str] = avg_skor_str
    evaluasi_keseluruhan_rerata["ringkasan_skor_rata_rata_per_variabel_gabungan"] = temp_ringkasan_skor_var_gabungan

    temp_detail_skor_ind_gabungan = []
    if hasattr(EvalGuru, 'pilihanvariabel'):
        for var_choice in EvalGuru.pilihanvariabel:
            var_id_int = var_choice[0]
            var_id_str = str(var_id_int)
            data_per_var_gabungan = {"variabel_id": var_id_int}
            
            # Dapatkan ID indikator yang relevan untuk variabel ini dari kunci-kunci yang ada di overall_scores_by_indicator
            # Urutkan berdasarkan nilai integer dari ID indikator (string)
            indicator_ids_for_this_var = sorted(
                overall_scores_by_indicator.get(var_id_str, {}).keys(),
                key=lambda k: int(k) if k.isdigit() else k # Urutkan numerik jika ID adalah digit
            )
            
            for ind_id_str in indicator_ids_for_this_var:
                skor_list = overall_scores_by_indicator.get(var_id_str, {}).get(ind_id_str, [])
                avg_skor_str = "- / 5.00"
                if skor_list: # Seharusnya selalu ada karena ind_id_str berasal dari keys
                    avg_skor = sum(skor_list) / len(skor_list)
                    avg_skor_str = f"{avg_skor:.2f} / 5.00"
                data_per_var_gabungan[f"Indikator {ind_id_str}"] = avg_skor_str
            temp_detail_skor_ind_gabungan.append(data_per_var_gabungan)
    evaluasi_keseluruhan_rerata["detail_skor_rata_rata_per_indikator_gabungan"] = temp_detail_skor_ind_gabungan

    if overall_kritik_saran_set:
        evaluasi_keseluruhan_rerata["daftar_kritik_saran_gabungan"] = sorted(list(overall_kritik_saran_set))
    if valid_overall_variable_scores_float:
        avg_grand_total_combined = sum(valid_overall_variable_scores_float) / len(valid_overall_variable_scores_float)
        evaluasi_keseluruhan_rerata["skor_grand_total_dari_variabel_gabungan"] = f"{avg_grand_total_combined:.2f} / 5.00"

    output_evaluasi_per_matapelajaran = []
    for mapel_id_key, data_mapel_agg in mapel_data_aggregator.items():
        matapelajaran_obj_mapel = data_mapel_agg['matapelajaran_obj']
        if not matapelajaran_obj_mapel: continue 

        total_pengisi_mapel = len(data_mapel_agg['unique_siswa_ids_mapel'])
        total_siswa_di_mapel = 0
        subject_detail_for_count = MataPelajaran.objects.filter(pk=matapelajaran_obj_mapel.id).annotate(num_students_mapel=Count('siswa_terdaftar', distinct=True)).first()
        if subject_detail_for_count:
            total_siswa_di_mapel = subject_detail_for_count.num_students_mapel
        kelas_display_str_mapel = ", ".join(sorted(list(data_mapel_agg['unique_kelas_names_mapel']))) if data_mapel_agg['unique_kelas_names_mapel'] else "N/A"

        mapel_scores_by_variable_specific = defaultdict(list)
        mapel_scores_by_indicator_specific = defaultdict(lambda: defaultdict(list))
        for isian_json_content in data_mapel_agg['parsed_isian_forms']:
            if isinstance(isian_json_content, dict):
                for var_id_str, indicators_data in isian_json_content.items():
                    if isinstance(indicators_data, dict):
                        for ind_id_str, skor_likert in indicators_data.items():
                            if isinstance(skor_likert, (int, float)) and 1 <= skor_likert <= 5:
                                skor_val = int(skor_likert)
                                mapel_scores_by_variable_specific[var_id_str].append(skor_val)
                                mapel_scores_by_indicator_specific[var_id_str][ind_id_str].append(skor_val)
        
        ringkasan_skor_per_var_mapel = {}
        if hasattr(EvalGuru, 'pilihanvariabel'):
            for var_choice in EvalGuru.pilihanvariabel:
                var_id_int_mapel = var_choice[0]
                var_id_str_mapel = str(var_id_int_mapel)
                skor_list_mapel = mapel_scores_by_variable_specific.get(var_id_str_mapel, [])
                avg_skor_str_mapel = "- / 5.00"
                if skor_list_mapel:
                    avg_skor_mapel = sum(skor_list_mapel) / len(skor_list_mapel)
                    avg_skor_str_mapel = f"{avg_skor_mapel:.2f} / 5.00"
                ringkasan_skor_per_var_mapel[var_id_str_mapel] = avg_skor_str_mapel

        detail_eval_ind_list_mapel = []
        if hasattr(EvalGuru, 'pilihanvariabel'):
            for var_choice in EvalGuru.pilihanvariabel:
                var_id_int_mapel = var_choice[0]
                var_id_str_mapel = str(var_id_int_mapel)
                data_per_var_mapel = {"variabel_id": var_id_int_mapel}
                
                indicator_ids_for_this_var_mapel = sorted(
                    mapel_scores_by_indicator_specific.get(var_id_str_mapel, {}).keys(),
                    key=lambda k: int(k) if k.isdigit() else k
                )
                
                for ind_id_str_mapel in indicator_ids_for_this_var_mapel:
                    skor_list_indikator = mapel_scores_by_indicator_specific.get(var_id_str_mapel, {}).get(ind_id_str_mapel, [])
                    avg_skor_str_indikator = "- / 5.00"
                    if skor_list_indikator:
                        avg_skor_indikator = sum(skor_list_indikator) / len(skor_list_indikator)
                        avg_skor_str_indikator = f"{avg_skor_indikator:.2f} / 5.00"
                    data_per_var_mapel[f"Indikator {ind_id_str_mapel}"] = avg_skor_str_indikator
                detail_eval_ind_list_mapel.append(data_per_var_mapel)
        
        all_kritik_saran_mapel = sorted(list(set(data_mapel_agg['kritik_saran_list_mapel'])))

        mapel_data_output_entry = {
            "matapelajaran_id": matapelajaran_obj_mapel.id,
            "nama_matapelajaran": matapelajaran_obj_mapel.nama if hasattr(matapelajaran_obj_mapel, 'nama') else "N/A",
            "total_pengisi_evaluasi": total_pengisi_mapel, 
            "total_siswa_di_matapelajaran": total_siswa_di_mapel,
            "daftar_kelas_evaluasi": kelas_display_str_mapel,
            "ringkasan_skor_per_variabel": ringkasan_skor_per_var_mapel,
            "detail_skor_per_indikator": detail_eval_ind_list_mapel,
            "daftar_kritik_saran": all_kritik_saran_mapel if all_kritik_saran_mapel else ["Tidak ada kritik/saran untuk mata pelajaran ini."]
        }
        output_evaluasi_per_matapelajaran.append(mapel_data_output_entry)

    output_evaluasi_per_matapelajaran = sorted(output_evaluasi_per_matapelajaran, key=lambda x: x['nama_matapelajaran'])

    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Detail evaluasi guru: ringkasan, per mata pelajaran, dan rerata gabungan.",
        "info_konteks": info_konteks,
        "evaluasi_per_matapelajaran": output_evaluasi_per_matapelajaran,
        "evaluasi_keseluruhan_rerata": evaluasi_keseluruhan_rerata
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentRole])
def get_cek_kelas(request, pk):
    try:
        siswa_id = request.user.id
        siswa_obj = Student.objects.get(pk=siswa_id)
        matpel_obj = MataPelajaran.objects.get(pk=pk)
        if isianEvalGuru.objects.filter(siswa=siswa_obj, matapelajaran=matpel_obj).exists():
            return JsonResponse({"status": status.HTTP_200_OK, "message": "Siswa sudah mengisi evaluasi untuk mata pelajaran ini."}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Siswa belum mengisi evaluasi untuk mata pelajaran ini."}, status=status.HTTP_400_BAD_REQUEST)
    except Student.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Siswa tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    except Kelas.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Kelas tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentRole])
def create_evalguru(request):
    try:
        data = request.data
        print("Data yang diterima:", data)  # Debugging line
        print(request.user)
        if not request.user.role != 'Student':
            return JsonResponse({"status": status.HTTP_403_FORBIDDEN, "message": "Hanya siswa yang dapat mengisi evaluasi."}, status=status.HTTP_403_FORBIDDEN)
        isian = data.get('isian')
        # isian -> {"1":{"1":3,"2":4}, "2":{1:5,"2":3}}
        kritik_saran = data.get('kritik_saran')
        siswa_id = request.user.id
        matapelajaran_id = data.get('matapelajaran_id')
        siswa_obj = Student.objects.get(pk=siswa_id)
        matapelajaran_obj = MataPelajaran.objects.get(pk=matapelajaran_id)
        c = False
        for i in matapelajaran_obj.siswa_terdaftar.all():
            if i.user_id == siswa_id:
                c = True
        if not c:
            return JsonResponse({"status": status.HTTP_403_FORBIDDEN, "message": "Siswa tidak terdaftar di mata pelajaran ini."}, status=status.HTTP_400_BAD_REQUEST)
        guru_obj = matapelajaran_obj.teacher
        if guru_obj is None:    
            return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Guru tidak ditemukan untuk mata pelajaran ini."}, status=status.HTTP_404_NOT_FOUND)
        if not siswa_obj or not guru_obj or not matapelajaran_obj:
            return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Siswa, guru, atau mata pelajaran tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
        
        existing_evaluations = isianEvalGuru.objects.filter(
            siswa=siswa_obj,
            guru=guru_obj,
            matapelajaran=matapelajaran_obj
        )
        if existing_evaluations.exists():
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Anda sudah mengisi evaluasi untuk guru ini di mata pelajaran ini."}, status=status.HTTP_400_BAD_REQUEST)

        evaluasi_guru = isianEvalGuru.objects.create(
            siswa=siswa_obj,
            guru=guru_obj,
            matapelajaran=matapelajaran_obj,
            isian=isian,
            kritik_saran=kritik_saran
        )

        return JsonResponse({"status": status.HTTP_201_CREATED, "message": "Evaluasi guru berhasil dibuat.", "evaluasi_id": evaluasi_guru.id}, status=status.HTTP_201_CREATED)
    except Student.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Siswa tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({"status": status, "message": f"Terjadi kesalahan: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_evaluasi_guru(request, pk):
    guru_id_str = request.user.id
    if not guru_id_str:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Hanya Guru pengajar itu sendiri yang dapat melihat!."}, status=status.HTTP_400_BAD_REQUEST)
    matapelajaran_id_str = pk

    try:
        guru_id = int(guru_id_str)
        matapelajaran_id = int(matapelajaran_id_str)
    except ValueError:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "ID guru dan ID mata pelajaran harus berupa angka."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guru_obj = Teacher.objects.get(user_id=guru_id)
        matapelajaran_obj = MataPelajaran.objects.get(id=matapelajaran_id)
    except Teacher.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Guru tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    except MataPelajaran.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Mata pelajaran tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    if matapelajaran_obj.teacher != guru_obj:
        return JsonResponse({"status": status.HTTP_403_FORBIDDEN, "message": "Hanya guru pengajar itu sendiri yang dapat melihat!"}, status=status.HTTP_403_FORBIDDEN)
    if not guru_obj or not matapelajaran_obj:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Guru atau mata pelajaran tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    evaluations = isianEvalGuru.objects.filter(
        guru=guru_obj,
        matapelajaran=matapelajaran_obj
    ).select_related('siswa', 'guru', 'matapelajaran')
    if not evaluations.exists():
        return JsonResponse({"status": status.HTTP_200_OK, "message": "Tidak ada data evaluasi untuk guru ini di mata pelajaran ini."}, status=status.HTTP_200_OK)
    response_data = []
    # Create data structures to hold our aggregated data
    scores_by_variable_indicator = defaultdict(lambda: defaultdict(list))
    all_kritik_saran = set()  # Using a set to avoid duplicates
    total_pengisi = 0

    # Collect data from all evaluations
    for evaluation in evaluations:
        total_pengisi += 1
        if evaluation.kritik_saran and evaluation.kritik_saran.strip():
            all_kritik_saran.add(evaluation.kritik_saran.strip())
        
        # Process the nested dictionary of scores
        if isinstance(evaluation.isian, dict):
            for var_id_str, indicators in evaluation.isian.items():
                if isinstance(indicators, dict):
                    for ind_id_str, score in indicators.items():
                        if isinstance(score, (int, float)) and 1 <= score <= 5:
                            scores_by_variable_indicator[var_id_str][ind_id_str].append(score)

    # Calculate averages per variable
    variable_averages = {}
    if hasattr(EvalGuru, 'pilihanvariabel'):
        for var_choice in EvalGuru.pilihanvariabel:
            var_id_int = var_choice[0]
            var_id_str = str(var_id_int)
            
            all_scores_for_var = []
            for scores in scores_by_variable_indicator.get(var_id_str, {}).values():
                all_scores_for_var.extend(scores)
            
            if all_scores_for_var:
                variable_averages[var_id_str] = f"{sum(all_scores_for_var) / len(all_scores_for_var):.2f} / 5.00"
            else:
                variable_averages[var_id_str] = "- / 5.00"

    # Calculate averages per indicator
    indicator_detail = []
    if hasattr(EvalGuru, 'pilihanvariabel'):
        for var_choice in EvalGuru.pilihanvariabel:
            var_id_int = var_choice[0]
            var_id_str = str(var_id_int)
            
            data_per_var = {"variabel_id": var_id_int}
            
            # Sort indicator IDs numerically
            indicator_ids = sorted(
                scores_by_variable_indicator.get(var_id_str, {}).keys(),
                key=lambda k: int(k) if k.isdigit() else k
            )
            
            for ind_id_str in indicator_ids:
                scores = scores_by_variable_indicator.get(var_id_str, {}).get(ind_id_str, [])
                if scores:
                    avg = sum(scores) / len(scores)
                    data_per_var[f"Indikator {ind_id_str}"] = f"{avg:.2f} / 5.00"
                else:
                    data_per_var[f"Indikator {ind_id_str}"] = "- / 5.00"
            
            indicator_detail.append(data_per_var)

    # Calculate grand total average
    valid_var_avgs = []
    for var_id_str in variable_averages.keys():
        all_var_scores = []
        for scores in scores_by_variable_indicator.get(var_id_str, {}).values():
            all_var_scores.extend(scores)
        if all_var_scores:
            valid_var_avgs.append(sum(all_var_scores) / len(all_var_scores))

    grand_total = f"{sum(valid_var_avgs) / len(valid_var_avgs):.2f} / 5.00" if valid_var_avgs else "- / 5.00"

    response_data = {
        "nama_matapelajaran": matapelajaran_obj.nama if hasattr(matapelajaran_obj, 'nama') else "N/A",
        "tahun_ajaran_mapel": str(matapelajaran_obj.tahunAjaran.tahunAjaran) if (hasattr(matapelajaran_obj, 'tahunAjaran') and matapelajaran_obj.tahunAjaran) else "N/A",
        "ringkasan_skor_rata_rata_per_variabel": variable_averages,
        "detail_skor_rata_rata_per_indikator": indicator_detail,
        "skor_grand_total": grand_total,
        "daftar_kritik_saran": sorted(list(all_kritik_saran)) if all_kritik_saran else ["Tidak ada kritik/saran."],
        "total_pengisi_evaluasi": total_pengisi,
        "total_siswa_diajar_di_matapelajaran": len(matapelajaran_obj.siswa_terdaftar.all()) if hasattr(matapelajaran_obj, 'siswa_terdaftar') else 0,
    }
    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Berhasil mendapatkan data evaluasi guru.",
        "evaluasi_guru": response_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherRole])
def get_evaluasi_guru_per_matpel(request):
    guru_id_str = request.user.id
    if not guru_id_str:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Hanya Guru pengajar itu sendiri yang dapat melihat!."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        guru_id = int(guru_id_str)
    except ValueError:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "ID guru harus berupa angka."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guru_obj = Teacher.objects.get(user_id=guru_id)
    except Teacher.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": "Guru tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    
    response_data = []
    all_mataPelajaran_obj = MataPelajaran.objects.filter(teacher=guru_obj)
    
    for matpel in all_mataPelajaran_obj:
        evaluation_per_class = isianEvalGuru.objects.filter(
            guru=guru_obj,
            matapelajaran=matpel
        )
        
        # Get total students registered in the course
        total_students = matpel.siswa_terdaftar.count() if hasattr(matpel, 'siswa_terdaftar') else 0
        
        # Count of unique students who submitted evaluations
        total_pengisi = evaluation_per_class.values('siswa').distinct().count()
        
        # Get tahun ajaran
        tahun_ajaran_str = str(matpel.tahunAjaran.tahunAjaran) if hasattr(matpel, 'tahunAjaran') and matpel.tahunAjaran else "N/A"
        
        # Initialize data structure for this mata pelajaran
        matpel_data = {
            "matapelajaran_id": matpel.id,
            "nama_matapelajaran": matpel.nama if hasattr(matpel, 'nama') else "N/A",
            "tahun_ajaran": tahun_ajaran_str,
            "total_siswa": total_students,
            "total_pengisi_evaluasi": total_pengisi,
            "skor_rata_rata": {}
        }
        
        # If there are evaluations, calculate average scores
        if evaluation_per_class.exists():
            scores_by_variable = defaultdict(list)
            
            # Collect all scores per variable
            for evaluation in evaluation_per_class:
                if isinstance(evaluation.isian, dict):
                    for var_id_str, indicators in evaluation.isian.items():
                        if isinstance(indicators, dict):
                            for _, score in indicators.items():
                                if isinstance(score, (int, float)) and 1 <= score <= 5:
                                    scores_by_variable[var_id_str].append(score)
            
            # Calculate average score for each variable
            for var_choice in EvalGuru.pilihanvariabel:
                var_id_int = var_choice[0]
                var_id_str = str(var_id_int)
                var_name = var_choice[1]
                
                scores = scores_by_variable.get(var_id_str, [])
                if scores:
                    avg_score = sum(scores) / len(scores)
                    matpel_data["skor_rata_rata"][var_name] = f"{avg_score:.2f} / 5.00"
                else:
                    matpel_data["skor_rata_rata"][var_name] = "- / 5.00"
        
        response_data.append(matpel_data)
    
    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Berhasil mendapatkan data evaluasi per mata pelajaran",
        "data": response_data
    }, status=status.HTTP_200_OK)