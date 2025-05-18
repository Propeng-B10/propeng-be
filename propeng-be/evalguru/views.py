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
    evaluations = EvalGuru.objects.select_related(
        'guru', 
        'matapelajaran',
        'siswa'     
    ).annotate(
        tahun_ajaran_str=F('siswa__siswa__tahunAjaran__tahunAjaran'), 
        nisp_guru=F('guru__nisp'),
        kelas_siswa_nama_annotated=F('siswa__siswa__namaKelas') 
    ).order_by('tahun_ajaran_str', 'guru__name') 

    if not evaluations.exists(): 
        return JsonResponse({
            "status": status.HTTP_200_OK, 
            "message": "Tidak ada data evaluasi.", 
            "data_evaluasi_per_tahun": {}
        }, status=status.HTTP_200_OK)

    raw_data_grouped = defaultdict(lambda: defaultdict(lambda: {
        'guru_id': None, 
        'nama_guru': None, 
        'nisp': None, 
        'mata_pelajaran_info_per_guru_ta': set(), 
        'evaluations_for_vars_per_guru_ta': defaultdict(list)
    }))

    for eval_entry in evaluations:
        ta_str_val = eval_entry.tahun_ajaran_str
        ta_key = str(ta_str_val) if ta_str_val is not None else "TA Tidak Diketahui"

        guru_id = eval_entry.guru_id
        current_guru_data = raw_data_grouped[ta_key][guru_id]

        if current_guru_data['guru_id'] is None:
            current_guru_data['guru_id'] = guru_id
            current_guru_data['nama_guru'] = eval_entry.guru.name if hasattr(eval_entry.guru, 'name') else "N/A" 
            current_guru_data['nisp'] = eval_entry.nisp_guru 
        
        mapel_str = eval_entry.matapelajaran.nama if hasattr(eval_entry.matapelajaran, 'nama') else "N/A"
        kelas_str = eval_entry.kelas_siswa_nama_annotated if eval_entry.kelas_siswa_nama_annotated else "N/A"
        
        # current_guru_data['mata_pelajaran_info_per_guru_ta'].add(f"{mapel_str} | {kelas_str}")
        current_guru_data['mata_pelajaran_info_per_guru_ta'].add(f"{mapel_str}")
        current_guru_data['evaluations_for_vars_per_guru_ta'][eval_entry.variabel].append(eval_entry.skorlikert)

    final_response_data = defaultdict(list)
    for ta_key, gurus_in_ta_data in raw_data_grouped.items():
        for guru_id, data_guru in gurus_in_ta_data.items():
            ta_filter_val = None
            if ta_key != "TA Tidak Diketahui":
                try:
                    ta_filter_val = int(ta_key) 
                except ValueError:
                    pass
            
            if ta_filter_val is not None:
                total_pengisi = EvalGuru.objects.filter(
                    guru_id=guru_id,
                    siswa__siswa__tahunAjaran__tahunAjaran=ta_filter_val
                ).values('siswa_id').distinct().count()
            else:
                 total_pengisi = EvalGuru.objects.filter(guru_id=guru_id).values('siswa_id').distinct().count()


            mapel_info_list = sorted(list(data_guru['mata_pelajaran_info_per_guru_ta']))
            mapel_summary_display = mapel_info_list 

            guru_output = {
                'guru_id': data_guru['guru_id'], 
                'nama_guru': data_guru['nama_guru'],
                'nisp': data_guru['nisp'], 
                'mata_pelajaran_summary': mapel_summary_display,
                'total_pengisi': total_pengisi, 
                'skor_per_variabel': {}
            }
            for variabel_choice in EvalGuru.pilihanvariabel: 
                var_id = variabel_choice[0] 
                skor_list = data_guru['evaluations_for_vars_per_guru_ta'].get(var_id, [])
                avg_skor = sum(skor_list) / len(skor_list) if skor_list else None
                guru_output['skor_per_variabel'][str(var_id)] = f"{avg_skor:.2f} / 5.00" if avg_skor is not None else "- / 5.00"
            final_response_data[ta_key].append(guru_output)

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
        tahun_ajaran_obj_exists = TahunAjaran.objects.filter(tahunAjaran=tahun_ajaran_value).exists()
        if not tahun_ajaran_obj_exists:
            raise TahunAjaran.DoesNotExist 
    except Teacher.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": f"Guru id {guru_id} tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
    except TahunAjaran.DoesNotExist:
        return JsonResponse({"status": status.HTTP_404_NOT_FOUND, "message": f"Tahun Ajaran dengan nilai '{tahun_ajaran_value}' tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

    info_konteks = {
        "guru_id": guru_obj.user_id, 
        "nama_guru": guru_obj.name if hasattr(guru_obj, 'name') else "N/A",
        "nisp": guru_obj.nisp if hasattr(guru_obj, 'nisp') else "N/A",
        "tahun_ajaran": str(tahun_ajaran_value)
    }

    evaluations_in_scope = EvalGuru.objects.filter(
        guru_id=guru_id,
        siswa__siswa__tahunAjaran__tahunAjaran=tahun_ajaran_value
    ).select_related('matapelajaran', 'siswa')

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
        
        kelas_siswa_str, _ = get_student_main_class_info(ev.siswa)
        if kelas_siswa_str != "N/A":
            evals_by_mapel[mapel_id]['unique_kelas_names'].add(kelas_siswa_str)
        
        if ev.kritik_saran:
            evals_by_mapel[mapel_id]['kritik_saran_per_siswa'][ev.siswa_id].add(ev.kritik_saran)

    output_evaluasi_per_matapelajaran = []

    for mapel_id, data in evals_by_mapel.items():
        matapelajaran_obj = data['matapelajaran_obj']
        entries_for_this_mapel = data['entries_for_mapel']
        
        kelas_display_str = ", ".join(sorted(list(data['unique_kelas_names']))) if data['unique_kelas_names'] else "N/A"
        
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
        for siswa_id, saran_set in data['kritik_saran_per_siswa'].items():
            all_kritik_saran_mapel.extend(list(saran_set))
        
        mapel_data_output = {
            "matapelajaran_id": matapelajaran_obj.id,
            "nama_matapelajaran": matapelajaran_obj.nama if hasattr(matapelajaran_obj, 'nama') else "N/A",
            "daftar_kelas_evaluasi": kelas_display_str,
            "ringkasan_skor_per_variabel": ringkasan_skor_per_variabel,
            "detail_skor_per_indikator": detail_evaluasi_indikator_list,
            "daftar_kritik_saran": all_kritik_saran_mapel if all_kritik_saran_mapel else ["Tidak ada kritik/saran untuk mata pelajaran ini."]
        }
        output_evaluasi_per_matapelajaran.append(mapel_data_output)

    output_evaluasi_per_matapelajaran = sorted(output_evaluasi_per_matapelajaran, key=lambda x: x['nama_matapelajaran'])

    return JsonResponse({
        "status": status.HTTP_200_OK,
        "message": "Detail evaluasi guru per mata pelajaran dalam tahun ajaran.",
        "info_konteks": info_konteks,
        "evaluasi_per_matapelajaran": output_evaluasi_per_matapelajaran
    }, status=status.HTTP_200_OK)