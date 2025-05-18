from django.http import JsonResponse
from evalguru.models import EvalGuru
from matapelajaran.models import MataPelajaran
from user.models import Teacher, Student
from kelas.models import Kelas 
from tahunajaran.models import TahunAjaran 
from django.db.models import Avg, F
from collections import defaultdict
from rest_framework.decorators import api_view
from django.db import transaction
from rest_framework import status


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
def get_overall_teacher_evaluations_overview(request):
    evaluations_base = EvalGuru.objects.select_related(
        'guru',
        'matapelajaran',
        'matapelajaran__tahunAjaran'
    ).annotate(
        tahun_ajaran_mapel_val=F('matapelajaran__tahunAjaran__tahunAjaran'),
        nisp_guru_val=F('guru__nisp')
    ).order_by('tahun_ajaran_mapel_val', 'guru__name')

    if not evaluations_base.exists():
        return JsonResponse({
            "status": status.HTTP_200_OK,
            "message": "Tidak ada data evaluasi.",
            "data_evaluasi_per_tahun": {}
        }, status=status.HTTP_200_OK)

    teacher_scores_by_ta = defaultdict(lambda: defaultdict(lambda: {
        'guru_id': None, 'nama_guru': None, 'nisp': None,
        'scores_per_variable': defaultdict(list)
    }))

    for ev in evaluations_base:
        ta_val = ev.tahun_ajaran_mapel_val
        ta_key = str(ta_val) if ta_val is not None else "TA Tidak Diketahui"
        gid = ev.guru_id

        teacher_data = teacher_scores_by_ta[ta_key][gid]
        if teacher_data['guru_id'] is None:
            teacher_data['guru_id'] = gid
            teacher_data['nama_guru'] = ev.guru.name if hasattr(ev.guru, 'name') else "N/A"
            teacher_data['nisp'] = ev.nisp_guru_val
        
        teacher_data['scores_per_variable'][ev.variabel].append(ev.skorlikert)

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

            pengisi_subquery = EvalGuru.objects.filter(
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
                num_siswa_terdaftar=Count('siswa_terdaftar', distinct=True),
                num_pengisi_eval=Subquery(pengisi_subquery[:1], output_field=IntegerField())
            ).order_by('nama') 

            detail_per_mata_pelajaran_list = []
            mata_pelajaran_summary_names_list = []

            for subject in subjects_with_counts:
                pengisi_count = subject.num_pengisi_eval if subject.num_pengisi_eval is not None else 0
                
                subject_display_name = subject.nama
                if subject.tahunAjaran and hasattr(subject.tahunAjaran, 'tahunAjaran'):
                    start_year = subject.tahunAjaran.tahunAjaran
                    # Membuat format seperti "Biologi Organik 2024/2025"
                    subject_display_name = f"{subject.nama}"
                    # subject_display_name = f"{subject.nama} {start_year}/{start_year + 1}"
                
                mata_pelajaran_summary_names_list.append(subject_display_name)
                
                detail_per_mata_pelajaran_list.append({
                    "matapelajaran_id": subject.id,
                    "nama_matapelajaran": subject_display_name, 
                    "total_pengisi_evaluasi": f"{pengisi_count}",
                    "total_siswa_mapel": f"{subject.num_siswa_terdaftar}",
                })
            
            # Pengurutan daftar nama dan detail mungkin lebih baik dilakukan setelah loop jika diperlukan urutan khusus
            # Jika pengurutan di query .order_by('nama') sudah cukup, list nama akan mengikuti urutan itu.

            skor_per_variabel_guru = {}
            for var_choice in EvalGuru.pilihanvariabel:
                var_id_str = str(var_choice[0])
                skor_list = teacher_info['scores_per_variable'].get(var_choice[0], [])
                avg_skor = sum(skor_list) / len(skor_list) if skor_list else None
                skor_per_variabel_guru[var_id_str] = f"{avg_skor:.2f} / 5.00" if avg_skor is not None else "- / 5.00"

            final_response_data[ta_key].append({
                "guru_id": teacher_info['guru_id'],
                "nama_guru": teacher_info['nama_guru'],
                "nisp": teacher_info['nisp'],
                "mata_pelajaran_summary": mata_pelajaran_summary_names_list, # Daftar nama
                "detail_per_mata_pelajaran": detail_per_mata_pelajaran_list, # Daftar objek detail
                "skor_per_variabel": skor_per_variabel_guru # Menggunakan key 'skor_per_variabel'
            })
            
    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Data evaluasi keseluruhan guru per tahun ajaran.", # Sesuai contoh user
        "data_evaluasi_per_tahun": final_response_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_teacher_evaluation_detail_page(request):
    guru_id_str = request.query_params.get('guru_id')
    tahun_ajaran_val_str = request.query_params.get('tahun_ajaran_id') # Ini adalah nilai tahun, misal 2025

    if not guru_id_str or not tahun_ajaran_val_str:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "Parameter guru_id dan tahun_ajaran_id (nilai tahun) diperlukan."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guru_id = int(guru_id_str)
        tahun_ajaran_value = int(tahun_ajaran_val_str) # Ini adalah nilai tahun (integer)
    except ValueError:
        return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "message": "ID guru dan nilai tahun ajaran harus berupa angka."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guru_obj = Teacher.objects.get(pk=guru_id)
        # Pastikan tahun ajaran ada di DB (Meskipun kita menggunakan nilainya untuk filter siswa)
        tahun_ajaran_obj_exists = TahunAjaran.objects.filter(tahunAjaran=tahun_ajaran_value).exists()
        if not tahun_ajaran_obj_exists:
            # Meskipun kita tidak menggunakan objek TahunAjaran secara langsung untuk query utama,
            # ada baiknya memastikan nilai tahun ajaran yang diberikan valid.
            raise TahunAjaran.DoesNotExist
    except Teacher.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": f"Guru id {guru_id} tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    except TahunAjaran.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": f"Tahun Ajaran dengan nilai '{tahun_ajaran_value}' tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

    info_konteks = {
        "guru_id": guru_obj.user_id, # Atau guru_obj.pk jika user_id adalah foreign key ke User
        "nama_guru": guru_obj.name if hasattr(guru_obj, 'name') else "N/A",
        "nisp": guru_obj.nisp if hasattr(guru_obj, 'nisp') else "N/A",
        "tahun_ajaran": str(tahun_ajaran_value)
    }

    # Filter evaluasi berdasarkan guru_id dan tahun ajaran siswa
    # Asumsi: evaluasi mengacu pada tahun ajaran siswa saat mengisi,
    # yang mana harusnya relevan dengan tahun ajaran mata pelajaran yang diajar guru.
    evaluations_in_scope = EvalGuru.objects.filter(
        guru_id=guru_id,
        # Filter berdasarkan tahun ajaran siswa yang melakukan evaluasi.
        # Ini mengasumsikan bahwa Kelas siswa memiliki foreign key ke TahunAjaran,
        # dan Student memiliki relasi ke Kelas.
        # Struktur model Student Anda adalah `student.kelas_set.filter(tahunAjaran__tahunAjaran=tahun_ajaran_value)`
        # atau jika siswa bisa di banyak kelas:
        # `siswa__kelas__tahunAjaran__tahunAjaran=tahun_ajaran_value`
        # Namun, karena EvalGuru sudah memiliki `siswa` (Student object),
        # dan Student memiliki `angkatan` yang mungkin terkait dengan `TahunAjaran`.
        # Untuk lebih presisi, kita perlu tahu bagaimana tahun ajaran evaluasi ditentukan.
        # Jika `MataPelajaran` memiliki `tahunAjaran` dan evaluasi selalu terkait `MataPelajaran` yang aktif di tahun itu:
        matapelajaran__tahunAjaran__tahunAjaran=tahun_ajaran_value
    ).select_related('matapelajaran', 'siswa') # siswa mungkin tidak perlu di sini jika hanya untuk count

    if not evaluations_in_scope.exists():
        return JsonResponse({
            "status": status.HTTP_200_OK,
            "message": f"Tidak ada evaluasi ditemukan untuk guru {guru_obj.name if hasattr(guru_obj, 'name') else 'N/A'} pada tahun ajaran {tahun_ajaran_value}.",
            "info_konteks": info_konteks,
            "evaluasi_per_matapelajaran": []
        }, status=status.HTTP_200_OK)

    evals_by_mapel = defaultdict(lambda: {
        'matapelajaran_obj': None,
        'entries_for_mapel': [],
        'unique_kelas_names': set(),
        'kritik_saran_per_siswa': defaultdict(set)
    })

    for ev in evaluations_in_scope:
        mapel_id = ev.matapelajaran_id
        if evals_by_mapel[mapel_id]['matapelajaran_obj'] is None:
            evals_by_mapel[mapel_id]['matapelajaran_obj'] = ev.matapelajaran

        evals_by_mapel[mapel_id]['entries_for_mapel'].append(ev)

        kelas_siswa_str, _ = get_student_main_class_info(ev.siswa) # Fungsi ini sudah ada
        if kelas_siswa_str != "N/A":
            evals_by_mapel[mapel_id]['unique_kelas_names'].add(kelas_siswa_str)

        if ev.kritik_saran:
            evals_by_mapel[mapel_id]['kritik_saran_per_siswa'][ev.siswa_id].add(ev.kritik_saran)

    output_evaluasi_per_matapelajaran = []

    for mapel_id, data in evals_by_mapel.items():
        matapelajaran_obj = data['matapelajaran_obj']
        entries_for_this_mapel = data['entries_for_mapel']

        kelas_display_str = ", ".join(sorted(list(data['unique_kelas_names']))) if data['unique_kelas_names'] else "N/A"

        # Menghitung total pengisi evaluasi unik untuk mata pelajaran ini
        # Kita menggunakan filter yang sama dengan `evaluations_in_scope` tapi spesifik untuk mapel_id ini
        # dan menghitung siswa_id yang unik.
        total_pengisi_mapel = EvalGuru.objects.filter(
            guru_id=guru_id,
            matapelajaran_id=matapelajaran_obj.id,
            matapelajaran__tahunAjaran__tahunAjaran=tahun_ajaran_value # atau filter tahun ajaran siswa jika lebih relevan
        ).values('siswa_id').distinct().count()

        # Menghitung total siswa yang terdaftar di mata pelajaran ini
        # Ini bergantung pada bagaimana siswa_terdaftar diisi di model MataPelajaran.
        # Jika siswa_terdaftar di MataPelajaran sudah spesifik untuk tahun ajaran dan guru tersebut, ini cukup.
        total_siswa_di_mapel = matapelajaran_obj.siswa_terdaftar.count()


        ringkasan_skor_per_variabel = {}
        skor_var_temp = defaultdict(list)
        for entry in entries_for_this_mapel:
            skor_var_temp[entry.variabel].append(entry.skorlikert)

        for var_choice in EvalGuru.pilihanvariabel:
            var_id = var_choice[0]
            skor_list = skor_var_temp.get(var_id, [])
            avg_skor = sum(skor_list) / len(skor_list) if skor_list else None
            ringkasan_skor_per_variabel[str(var_id)] = f"{avg_skor:.2f} / 5.00" if avg_skor is not None else "- / 5.00"

        detail_evaluasi_indikator_list = []
        skor_var_ind_temp = defaultdict(lambda: defaultdict(list))
        for entry in entries_for_this_mapel:
            skor_var_ind_temp[entry.variabel][entry.indikator].append(entry.skorlikert)

        for var_choice in EvalGuru.pilihanvariabel:
            var_id = var_choice[0]
            data_per_variabel = {"variabel_id": var_id}
            for ind_choice in EvalGuru.pilihanindikator:
                ind_id = ind_choice[0]
                skor_list = skor_var_ind_temp.get(var_id, {}).get(ind_id, [])
                avg_skor = sum(skor_list) / len(skor_list) if skor_list else None
                data_per_variabel[f"Indikator {ind_id}"] = f"{avg_skor:.2f} / 5.00" if avg_skor is not None else "- / 5.00"
            detail_evaluasi_indikator_list.append(data_per_variabel)

        all_kritik_saran_mapel = []
        for siswa_id_kritik, saran_set in data['kritik_saran_per_siswa'].items(): 
            all_kritik_saran_mapel.extend(list(saran_set))

        mapel_data_output = {
            "matapelajaran_id": matapelajaran_obj.id,
            "nama_matapelajaran": matapelajaran_obj.nama if hasattr(matapelajaran_obj, 'nama') else "N/A",
            "total_pengisi_evaluasi": total_pengisi_mapel,
            "total_siswa_di_matapelajaran": total_siswa_di_mapel,
            "daftar_kelas_evaluasi": kelas_display_str,
            "ringkasan_skor_per_variabel": ringkasan_skor_per_variabel,
            "detail_skor_per_indikator": detail_evaluasi_indikator_list,
            "daftar_kritik_saran": all_kritik_saran_mapel if all_kritik_saran_mapel else ["Tidak ada kritik/saran untuk mata pelajaran ini."]
        }
        output_evaluasi_per_matapelajaran.append(mapel_data_output)

    # Urutkan berdasarkan nama mata pelajaran jika diperlukan
    output_evaluasi_per_matapelajaran = sorted(output_evaluasi_per_matapelajaran, key=lambda x: x['nama_matapelajaran'])

    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Detail evaluasi guru per mata pelajaran dalam tahun ajaran.",
        "info_konteks": info_konteks,
        "evaluasi_per_matapelajaran": output_evaluasi_per_matapelajaran
    }, status=status.HTTP_200_OK)
