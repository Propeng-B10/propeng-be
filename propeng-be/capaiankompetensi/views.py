# capaiankompetensi/views.py

import json
from urllib import response
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

# Impor model
from matapelajaran.models import MataPelajaran # SESUAIKAN PATH
from .models import CapaianKompetensi

# Fungsi serialisasi paling ramping
def serialize_capaian_paling_ramping(capaian):
    if not capaian:
        return None
    return {
        'deskripsi': capaian.deskripsi,
    }
def drf_error_response(message, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({'message': message, 'error': True}, status=http_status)
@csrf_exempt
@require_http_methods(["GET", "POST"])
@transaction.atomic # Pastikan semua operasi (update/create/delete) atomic
def capaian_api_view(request, mapel_pk):
    """
    API Endpoint untuk:
    - GET: Mendapatkan Deskripsi Pengetahuan & Keterampilan.
    - POST: Membuat/Mengupdate/Menghapus Deskripsi Pengetahuan dan/atau Keterampilan.
            Body JSON:
            - {"pengetahuan": "string"} -> Upsert Pengetahuan
            - {"keterampilan": "string"} -> Upsert Keterampilan
            - {"pengetahuan": null} -> Delete Pengetahuan
            - {"keterampilan": null} -> Delete Keterampilan
            (Kunci bisa dikombinasikan, minimal satu kunci harus ada)
    """
    try:
        mata_pelajaran = MataPelajaran.objects.get(pk=mapel_pk)
    except MataPelajaran.DoesNotExist:
         return HttpResponseNotFound(json.dumps({'error': f'Mata Pelajaran id {mapel_pk} tidak ditemukan.'}), content_type="application/json")
    except ValueError:
        return HttpResponseNotFound(json.dumps({'error': 'ID Mata Pelajaran tidak valid.'}), content_type="application/json")

    # --- Logika GET ---
    if request.method == 'GET':
        # ... (Logika GET tetap sama seperti sebelumnya) ...
        capaian_pengetahuan = CapaianKompetensi.objects.filter(
            mata_pelajaran=mata_pelajaran,
            tipe=CapaianKompetensi.PENGETAHUAN
        ).first()
        capaian_keterampilan = CapaianKompetensi.objects.filter(
            mata_pelajaran=mata_pelajaran,
            tipe=CapaianKompetensi.KETERAMPILAN
        ).first()
        response_data = {
            'pengetahuan': serialize_capaian_paling_ramping(capaian_pengetahuan),
            'keterampilan': serialize_capaian_paling_ramping(capaian_keterampilan)
        }
        return JsonResponse(response_data)

    # --- Logika POST (Upsert / Delete) ---
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict):
                raise json.JSONDecodeError("Request body harus objek JSON.", request.body, 0)
        except json.JSONDecodeError as e:
            return HttpResponseBadRequest(json.dumps({'error': f'Format JSON body tidak valid: {e}'}), content_type="application/json")

        # Cek apakah setidaknya satu kunci yang relevan ada di body
        if 'pengetahuan' not in data and 'keterampilan' not in data:
            return HttpResponseBadRequest(json.dumps({'error': 'Request body JSON harus berisi kunci "pengetahuan" dan/atau "keterampilan".'}), content_type="application/json")

        try:
            # Proses Pengetahuan jika kuncinya ada di request body
            if 'pengetahuan' in data:
                nilai_p = data['pengetahuan']
                if nilai_p is None:
                    # --- Hapus Pengetahuan ---
                    deleted_count, _ = CapaianKompetensi.objects.filter(
                        mata_pelajaran=mata_pelajaran,
                        tipe=CapaianKompetensi.PENGETAHUAN
                    ).delete()
                    # deleted_count akan 0 jika tidak ada yg dihapus, 1 jika berhasil dihapus
                elif isinstance(nilai_p, str):
                    # --- Update atau Create Pengetahuan ---
                    obj_p, created_p = CapaianKompetensi.objects.update_or_create(
                        mata_pelajaran=mata_pelajaran,
                        tipe=CapaianKompetensi.PENGETAHUAN,
                        defaults={'deskripsi': nilai_p}
                    )
                else:
                    # Tipe data selain string atau null tidak valid
                    return HttpResponseBadRequest(json.dumps({'error': 'Nilai untuk "pengetahuan" harus berupa string atau null (untuk hapus).'}), content_type="application/json")

            # Proses Keterampilan jika kuncinya ada di request body
            if 'keterampilan' in data:
                nilai_k = data['keterampilan']
                if nilai_k is None:
                    # --- Hapus Keterampilan ---
                    deleted_count_k, _ = CapaianKompetensi.objects.filter(
                        mata_pelajaran=mata_pelajaran,
                        tipe=CapaianKompetensi.KETERAMPILAN
                    ).delete()
                elif isinstance(nilai_k, str):
                    # --- Update atau Create Keterampilan ---
                    obj_k, created_k = CapaianKompetensi.objects.update_or_create(
                        mata_pelajaran=mata_pelajaran,
                        tipe=CapaianKompetensi.KETERAMPILAN,
                        defaults={'deskripsi': nilai_k}
                    )
                else:
                     # Tipe data selain string atau null tidak valid
                    return HttpResponseBadRequest(json.dumps({'error': 'Nilai untuk "keterampilan" harus berupa string atau null (untuk hapus).'}), content_type="application/json")

        except Exception as e:
             # Tangkap error tak terduga saat operasi database
             # print(f"Error during POST operation: {e}") # Ganti dengan logging
             return JsonResponse({'error': f'Terjadi kesalahan internal server saat memproses data.'}, status=500)

        # Setelah semua operasi (update/create/delete) selesai, fetch state terbaru
        final_pengetahuan = CapaianKompetensi.objects.filter(mata_pelajaran=mata_pelajaran, tipe=CapaianKompetensi.PENGETAHUAN).first()
        final_keterampilan = CapaianKompetensi.objects.filter(mata_pelajaran=mata_pelajaran, tipe=CapaianKompetensi.KETERAMPILAN).first()

        # Kembalikan state terbaru dengan status 200 OK
        response_data = {
            'pengetahuan': serialize_capaian_paling_ramping(final_pengetahuan),
            'keterampilan': serialize_capaian_paling_ramping(final_keterampilan)
        }
        return JsonResponse(response_data, status=200)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Keep it simple for now
def get_capaian_descriptions_for_subject(request: Request, matapelajaran_id: int):
    """
    Retrieves the Pengetahuan and Keterampilan competency descriptions
    for a specific Mata Pelajaran.
    """
    try:
        # 1. Get the Mata Pelajaran object
        try:
            mata_pelajaran = MataPelajaran.objects.get(pk=matapelajaran_id)
        except MataPelajaran.DoesNotExist:
            return drf_error_response(f"Mata Pelajaran dengan ID {matapelajaran_id} tidak ditemukan.", status.HTTP_404_NOT_FOUND)
        except ValueError: # Handle non-integer IDs if they somehow get past URLconf
             return drf_error_response("ID Mata Pelajaran tidak valid.", status.HTTP_400_BAD_REQUEST)

        # Optional: Add permission check - e.g., is student enrolled? is teacher assigned?
        # For now, just checks authentication.

        # 2. Fetch the related Capaian Kompetensi objects
        capaian_pengetahuan = CapaianKompetensi.objects.filter(
            mata_pelajaran=mata_pelajaran,
            tipe=CapaianKompetensi.PENGETAHUAN
        ).first() # Get the first (should be only one) or None

        capaian_keterampilan = CapaianKompetensi.objects.filter(
            mata_pelajaran=mata_pelajaran,
            tipe=CapaianKompetensi.KETERAMPILAN
        ).first() # Get the first or None

        # 3. Prepare the response data
        response_data = {
            "matapelajaran_id": mata_pelajaran.id,
            "matapelajaran_nama": mata_pelajaran.nama,
            "capaian_pengetahuan": capaian_pengetahuan.deskripsi if capaian_pengetahuan else None,
            "capaian_keterampilan": capaian_keterampilan.deskripsi if capaian_keterampilan else None,
        }

        return Response({
            "status": 200,
            "message": "Capaian kompetensi berhasil diambil.",
            "data": response_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Log the error details for debugging
        print(f"Error fetching capaian kompetensi for subject {matapelajaran_id}: {e}")
        import traceback
        traceback.print_exc()
        return drf_error_response("Terjadi kesalahan internal server.", status.HTTP_500_INTERNAL_SERVER_ERROR)
