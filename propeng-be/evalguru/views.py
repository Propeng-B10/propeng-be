from django.shortcuts import render
from django.http import JsonResponse
from models import EvalGuru, MataPelajaran
from django.db.models import Avg, F
from collections import defaultdict # Untuk mengelompokkan data
from rest_framework.decorators import api_view

@api_view(['POST'])
def siswafill_evalguru(request):
    data = request.data
    siswa_id = data.get('siswa_id')
    guru_id = data.get('guru_id')
    matapelajaran_id = data.get('matapelajaran_id')
    indikator = data.get('indikator')
    variabel = data.get('variabel')
    skorlikert = data.get('skorlikert')

    evaluasi_guru = EvalGuru.objects.create(
        siswa_id=siswa_id,
        guru_id=guru_id,
        matapelajaran_id=matapelajaran_id,
        indikator=indikator,
        variabel=variabel,
        skorlikert=skorlikert
    )

    evaluasi_guru.save()
    
    nama_siswa = evaluasi_guru.siswa.nama
    nama_guru = evaluasi_guru.guru.nama
    nama_matapelajaran = evaluasi_guru.matapelajaran.nama
    kelas_matapelajaran = evaluasi_guru.matapelajaran.kelas.nama
    tahun_ajaran_matapelajaran = evaluasi_guru.matapelajaran.tahun_ajaran.tahun_ajaran

    return JsonResponse({
        "status": 200,
        "data": {
            "id": evaluasi_guru.id,
            "siswa_id": evaluasi_guru.siswa_id,
            "siswa_nama": nama_siswa,
            "guru_id": evaluasi_guru.guru_id,
            "guru_nama": nama_guru,
            "matapelajaran_id": evaluasi_guru.matapelajaran_id,
            "matapelajaran_nama": nama_matapelajaran,
            "matapelajaran_kelas": kelas_matapelajaran,
            "matapelajaran_tahun_ajaran": tahun_ajaran_matapelajaran,
            "indikator": evaluasi_guru.indikator,
            "variabel": evaluasi_guru.variabel,
            "skorlikert": evaluasi_guru.skorlikert
        },
        "message": "Berhasil mengisi evaluasi guru",
    })


@api_view(['GET'])
def guru_get_evalguru_in_mapel(request):
    guru_id = request.data.get('guru_id')
    matapelajaran_id = request.data.get('matapelajaran_id')

    if not guru_id or not matapelajaran_id:
        return JsonResponse({
            "status": 400,
            "message": "Bad Request: guru_id dan matapelajaran_id diperlukan.",
        }, status=400)

    try:
        guru_id = int(guru_id)
        matapelajaran_id = int(matapelajaran_id)
    except ValueError:
        return JsonResponse({
            "status": 400,
            "message": "Bad Request: guru_id dan matapelajaran_id harus berupa angka.",
        }, status=400)

    try:
        matapelajaran = MataPelajaran.objects.select_related('kelas', 'tahun_ajaran').get(id=matapelajaran_id)
        nama_matapelajaran = matapelajaran.nama
        nama_kelas = matapelajaran.kelas.nama if hasattr(matapelajaran, 'kelas') and matapelajaran.kelas else "N/A"
        tahun_ajaran = matapelajaran.tahun_ajaran.tahun_ajaran if hasattr(matapelajaran, 'tahun_ajaran') and matapelajaran.tahun_ajaran else "N/A"
    except MataPelajaran.DoesNotExist:
        return JsonResponse({
            "status": 404,
            "message": "Data Mata Pelajaran tidak ditemukan.",
        }, status=404)
    except AttributeError:
        nama_kelas = getattr(getattr(matapelajaran, 'kelas', None), 'nama', "N/A")
        tahun_ajaran = getattr(getattr(matapelajaran, 'tahun_ajaran', None), 'tahun_ajaran', "N/A")

    evaluasi_aggregat = EvalGuru.objects.filter(
        guru_id=guru_id,
        matapelajaran_id=matapelajaran_id
    ).values(
        'variabel', 'indikator'
    ).annotate(
        avg_skor=Avg('skorlikert')
    ).order_by('variabel', 'indikator')

    skor_map = {(item['variabel'], item['indikator']): item['avg_skor'] for item in evaluasi_aggregat}

    hasil_evaluasi_list = []
    # [(1,1), (2,2), (3,3), (4,4), (5,5)] ... 
    for variabel_choice in EvalGuru.pilihanvariabel:
        var_id = variabel_choice[0] 

        data_per_variabel = {
            "variabel_id": var_id
        }
        for indikator_choice in EvalGuru.pilihanindikator:
            indicator_id = indikator_choice[0]
            rata_rata = skor_map.get((var_id, indicator_id))
            if rata_rata is not None:
                data_per_variabel[f"Indikator {indicator_id}"] = f"{rata_rata:.2f} / 5"
            else:
                data_per_variabel[f"Indikator {indicator_id}"] = "- / 5"
        hasil_evaluasi_list.append(data_per_variabel)

    return JsonResponse({
        "status": 200,
        "message": "Berhasil mendapatkan data evaluasi guru",
        "nama_matapelajaran": nama_matapelajaran,
        "nama_kelas": nama_kelas,
        "tahun_ajaran": tahun_ajaran,
        "hasil_evaluasi": hasil_evaluasi_list,
    })



@api_view(['GET'])
def guru_get_all_evaluations_summary(request):
    data = request.data
    guru_id = data.get('guru_id')

    if not guru_id:
        return JsonResponse({
            "status": 400,
            "message": "Bad Request: guru_id diperlukan sebagai query parameter.",
        }, status=400)

    try:
        guru_id = int(guru_id)
    except ValueError:
        return JsonResponse({
            "status": 400,
            "message": "Bad Request: guru_id harus berupa angka.",
        }, status=400)

    matapelajaran_ids_evaluasi = EvalGuru.objects.filter(guru_id=guru_id)\
                                            .values_list('matapelajaran_id', flat=True)\
                                            .distinct()

    if not matapelajaran_ids_evaluasi:
        return JsonResponse({
            "status": 200,
            "message": "Tidak ada data evaluasi ditemukan untuk guru ini.",
            "data_evaluasi": []
        })

    mapel_objects_list = MataPelajaran.objects.filter(id__in=matapelajaran_ids_evaluasi)\
                                            .select_related('kelas', 'tahun_ajaran')\
                                            .order_by('nama', 'kelas__nama', 'tahun_ajaran__tahun_ajaran')

    all_mapel_summary_data = []

    for mapel in mapel_objects_list:
        mapel_summary = {
            "matapelajaran_id": mapel.id,
            "nama_matapelajaran": mapel.nama,
            "nama_kelas": mapel.kelas.nama if hasattr(mapel, 'kelas') and mapel.kelas else "N/A",
            "tahun_ajaran": mapel.tahun_ajaran.tahun_ajaran if hasattr(mapel, 'tahun_ajaran') and mapel.tahun_ajaran else "N/A",
            "skor_per_variabel": {}
        }

        for variabel_choice in EvalGuru.pilihanvariabel:
            var_id = variabel_choice[0]  

            skor_data = EvalGuru.objects.filter(
                guru_id=guru_id,
                matapelajaran_id=mapel.id,
                variabel=var_id 
            ).aggregate(avg_skor=Avg('skorlikert'))

            avg_skor_value = skor_data.get('avg_skor')

            if avg_skor_value is not None:
                mapel_summary["skor_per_variabel"][str(var_id)] = f"{avg_skor_value:.2f} / 5"
            else:
                mapel_summary["skor_per_variabel"][str(var_id)] = "- / 5"
        
        all_mapel_summary_data.append(mapel_summary)

    return JsonResponse({
        "status": 200,
        "message": "Berhasil mendapatkan rangkuman data evaluasi untuk semua mata pelajaran guru.",
        "data_evaluasi": all_mapel_summary_data
    })



@api_view(['GET'])
def get_overall_teacher_evaluations_overview(request):
    # Tidak ada input guru_id atau tahun_ajaran spesifik, mengambil semua
    
    # 1. Semua entri evaluasi beserta informasi terkait
    evaluations = EvalGuru.objects.select_related(
        'guru', 
        'matapelajaran__tahun_ajaran',
        'matapelajaran__kelas',
        'matapelajaran' 
    ).annotate(
        tahun_ajaran_str=F('matapelajaran__tahun_ajaran__tahun_ajaran'),
        nip_guru=F('guru__nip') 
    ).order_by('tahun_ajaran_str', 'guru__nama')

    if not evaluations.exists():
        return JsonResponse({
            "status": 200,
            "message": "Tidak ada data evaluasi ditemukan.",
            "data_evaluasi_per_tahun": {}
        })

    raw_data_grouped = defaultdict(lambda: defaultdict(lambda: {
        'guru_id': None,
        'nama_guru': None,
        'nip_nisn': None,
        'mata_pelajaran_info': set(), 
        'evaluations_for_vars': defaultdict(list) 
    }))

    for eval_entry in evaluations:
        ta_str = eval_entry.tahun_ajaran_str
        if not ta_str: 
            continue

        guru_id = eval_entry.guru_id
        
        current_guru_data = raw_data_grouped[ta_str][guru_id]

        if current_guru_data['guru_id'] is None:
            current_guru_data['guru_id'] = guru_id
            current_guru_data['nama_guru'] = eval_entry.guru.nama
            current_guru_data['nip_nisn'] = eval_entry.nip_guru # Pastikan field NIP benar

        mapel_str = eval_entry.matapelajaran.nama
        kelas_str = eval_entry.matapelajaran.kelas.nama if eval_entry.matapelajaran.kelas else "N/A"
        current_guru_data['mata_pelajaran_info'].add(f"{mapel_str} (Kelas {kelas_str})")
        
        
        current_guru_data['evaluations_for_vars'][eval_entry.variabel].append(eval_entry.skorlikert)

    final_response_data = defaultdict(list)

    for ta_str, gurus_in_ta_data in raw_data_grouped.items():
        for guru_id, data_guru in gurus_in_ta_data.items():
            
            total_pengisi = EvalGuru.objects.filter(
                guru_id=guru_id,
                matapelajaran__tahun_ajaran__tahun_ajaran=ta_str
            ).values('siswa_id').distinct().count()

            mapel_info_list = sorted(list(data_guru['mata_pelajaran_info']))
            mapel_summary_str = ", ".join(mapel_info_list[:2])
            if len(mapel_info_list) > 2:
                mapel_summary_str += f", +{len(mapel_info_list) - 2}"

            guru_output = {
                'guru_id': data_guru['guru_id'],
                'nama_guru': data_guru['nama_guru'],
                'nip_nisn': data_guru['nip_nisn'],
                'mata_pelajaran_summary': mapel_summary_str,
                'total_pengisi': total_pengisi,
                'skor_per_variabel': {}
            }

            for variabel_choice in EvalGuru.pilihanvariabel:
                var_id = variabel_choice[0] 
                
                skor_list = data_guru['evaluations_for_vars'].get(var_id, [])
                if skor_list:
                    avg_skor = sum(skor_list) / len(skor_list)
                    guru_output['skor_per_variabel'][str(var_id)] = f"{avg_skor:.2f} / 5"
                else:
                    guru_output['skor_per_variabel'][str(var_id)] = "- / 5"
            
            final_response_data[ta_str].append(guru_output)

    return JsonResponse({
        "status": 200,
        "message": "Berhasil mendapatkan data evaluasi keseluruhan guru per tahun ajaran.",
        "data_evaluasi_per_tahun": final_response_data
    })
