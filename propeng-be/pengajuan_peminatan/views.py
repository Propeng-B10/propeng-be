from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import *
from user.models import User
from django.db import connection
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    print("error disini")
    print(request)
    print("🔹 create event")
    data = request.data
    print(data)
    startdate = data.get('start_date')
    enddate = data.get('end_date')
    angkatan = data.get('angkatan')
    idid_matpel = data.get('matpels')
    # ekspektasinya, isi dari idid matpel ini berupa list id, dari t1o1 sampai t4o2
    # berupa [1,2,3,4,...,8] 
    angkatan = Angkatan.objects.get(id=angkatan)

    capaciti_matpel = data.get('capacity')
    # ekspektasinya, isi dari capacity ini jg mirip, berupa list capacity int, dari t1o1 sampai t4o2
    # berupa [1,2,3,4, dst] 
    for i in capaciti_matpel:
        i = int(i)
    matpelObj = []
    for i in idid_matpel:
        matpel = MataPelajaran.objects.get(id=int(i))
        matpelObj.append(matpel)

    event = Event.objects.create(start_date=startdate,end_date=enddate,angkatan=angkatan,
                                 tier1_option1=matpelObj[0],tier1_option2=matpelObj[1],
                                 tier2_option1=matpelObj[2],tier2_option2=matpelObj[3],
                                 tier3_option1=matpelObj[4],tier3_option2=matpelObj[5],
                                 tier4_option1=matpelObj[6],tier4_option2=matpelObj[7],
                                 t1o1_capacity=capaciti_matpel[0], t1o2_capacity=capaciti_matpel[1],
                                 t2o1_capacity=capaciti_matpel[2], t2o2_capacity=capaciti_matpel[3],
                                 t3o1_capacity=capaciti_matpel[4], t3o2_capacity=capaciti_matpel[5],
                                 t4o1_capacity=capaciti_matpel[6], t4o2_capacity=capaciti_matpel[7])
    data_event = {
        "start_date" : event.start_date,
        "end_date" : event.end_date,
        "angkatan" : f"angkatan {event.angkatan}"
    }
    
    return Response({
                "status": 201,
                "message": "Event berhasil dibuat dengan sukses!",
                "data": data_event
            }, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_pilihan_siswa(request):
    print("🔹 create pilihan siswa")
    try:
        data = request.data
        
        event_id = data.get('event_id')
        student_id = data.get('student_id')
        tier1 = data.get('tier1')
        tier2 = data.get('tier2')
        tier3 = data.get('tier3')
        tier4 = data.get('tier4')
        
        if None in [event_id, student_id, tier1, tier2, tier3, tier4]:
            return Response({
                "status": 400,
                "message": "Data tidak lengkap",
                "error": "Semua kolom (event_id, student_id, tier1, tier2, tier3, tier4) wajib diisi"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tier1_bool = bool(tier1)
        tier2_bool = bool(tier2)
        tier3_bool = bool(tier3)
        tier4_bool = bool(tier4)
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Event tidak ditemukan",
                "error": f"Event dengan ID {event_id} tidak ditemukan"
            }, status=status.HTTP_404_NOT_FOUND)
            
        current_date = timezone.now().date()
        if current_date < event.start_date:
            return Response({
                "status": 400,
                "message": "Event belum dimulai",
                "error": f"Pengajuan peminatan baru dimulai pada {event.start_date}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if current_date > event.end_date:
            return Response({
                "status": 400,
                "message": "Event sudah berakhir",
                "error": f"Pengajuan peminatan telah berakhir pada {event.end_date}"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            student = Student.objects.get(user_id=student_id)
        except Student.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Siswa tidak ditemukan",
                "error": f"Siswa dengan ID {student_id} tidak ditemukan"
            }, status=status.HTTP_404_NOT_FOUND)
        
        existing_choice = PilihanSiswa.objects.filter(event=event, student=student).first()
        if existing_choice:
            return Response({
                "status": 400,
                "message": "Siswa sudah memiliki pilihan untuk event ini",
                "error": "Tidak dapat membuat pilihan duplikat"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pilihan_siswa = PilihanSiswa.objects.create(
            event=event,
            student=student,
            tier1=tier1_bool,
            tier2=tier2_bool,
            tier3=tier3_bool,
            tier4=tier4_bool,
        )
        
        response_data = {
            "id": pilihan_siswa.id,
            "event_id": event.id,
            "student_id": student.user_id,
            "student_username": f"{student.username}",
            "tier1": pilihan_siswa.tier1,
            "tier2": pilihan_siswa.tier2,
            "tier3": pilihan_siswa.tier3,
            "tier4": pilihan_siswa.tier4,
            "submitted_at": pilihan_siswa.submitted_at
        }
        
        return Response({
            "status": 201,
            "message": "Pilihan siswa berhasil disimpan",
            "data": response_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": "Terjadi kesalahan",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_pilihan_siswa(request):
    print("🔹 update pilihan siswa")
    try:
        data = request.data
        note = data.get("note")
        
        pilihan_id = data.get('pilihan_id')
        if not pilihan_id:
            return Response({
                "status": 400,
                "message": "Data tidak lengkap",
                "error": "pilihan_id wajib diisi"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pilihan_siswa = PilihanSiswa.objects.get(id=pilihan_id)
        except PilihanSiswa.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Pilihan siswa tidak ditemukan",
                "error": f"PilihanSiswa dengan ID {pilihan_id} tidak ditemukan"
            }, status=status.HTTP_404_NOT_FOUND)
        
        tier1 = data.get('tier1')
        tier2 = data.get('tier2')
        tier3 = data.get('tier3')
        tier4 = data.get('tier4')
        
        if tier1 is not None:
            pilihan_siswa.tier1 = bool(tier1)
        if tier2 is not None:
            pilihan_siswa.tier2 = bool(tier2)
        if tier3 is not None:
            pilihan_siswa.tier3 = bool(tier3)
        if tier4 is not None:
            pilihan_siswa.tier4 = bool(tier4)
        
        if tier1 is not None:
            pilihan_siswa.statustier1 = None
        if tier2 is not None:
            pilihan_siswa.statustier2 = None
        if tier3 is not None:
            pilihan_siswa.statustier3 = None
        if tier4 is not None:
            pilihan_siswa.statustier4 = None
            
        pilihan_siswa.submitted_at = timezone.now()
        
        if note is not None:
            pilihan_siswa.note = note
        else:
            pilihan_siswa.note = "Tidak ada catatan dari Wali Kelas"

        pilihan_siswa.save()
        
        response_data = {
            "id": pilihan_siswa.id,
            "event_id": pilihan_siswa.event.id,
            "student_id": pilihan_siswa.student.user_id,
            "student_username": f"{pilihan_siswa.student.username}",
            "tier1": pilihan_siswa.tier1,
            "tier2": pilihan_siswa.tier2,
            "tier3": pilihan_siswa.tier3,
            "tier4": pilihan_siswa.tier4,
            "submitted_at": pilihan_siswa.submitted_at
        }
        
        return Response({
            "status": 200,
            "message": "Pilihan siswa berhasil diupdate",
            "data": response_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": 500,
            "message": "Terjadi kesalahan",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_event(request):
    print("🔹 get active event for user")
    try:
        user = request.user
        
        try:
            student = Student.objects.get(user=user)
        except Student.DoesNotExist:
            return Response({
                "status": 403,
                "message": "Akses ditolak",
                "error": "Hanya siswa yang dapat mengakses endpoint ini"
            }, status=status.HTTP_403_FORBIDDEN)
        
        angkatan = student.angkatan
        
        current_date = timezone.now().date()
        
        active_events = Event.objects.filter(
            (Q(angkatan=angkatan)) &
            (Q(start_date__lte=current_date) & Q(end_date__gte=current_date))
        ).order_by('-start_date')
        
        if not active_events.exists():
            future_events = Event.objects.filter(
                (Q(angkatan=angkatan)) &
                (Q(start_date__gt=current_date))
            ).order_by('start_date')
            
            if future_events.exists():
                future_event = future_events.first()
                return Response({
                    "status": 200,
                    "message": "Event yang akan datang ditemukan",
                    "data": {
                        "event_exists": True,
                        "is_active": False,
                        "event_id": future_event.id,
                        "start_date": future_event.start_date,
                        "end_date": future_event.end_date,
                        "status": "akan_datang"
                    }
                }, status=status.HTTP_200_OK)
            
            past_events = Event.objects.filter(
                (Q(angkatan=angkatan)) &
                (Q(end_date__lt=current_date))
            ).order_by('-end_date')
            
            if past_events.exists():
                past_event = past_events.first()
                return Response({
                    "status": 200,
                    "message": "Event yang telah berlalu ditemukan",
                    "data": {
                        "event_exists": True,
                        "is_active": False,
                        "event_id": past_event.id,
                        "start_date": past_event.start_date,
                        "end_date": past_event.end_date,
                        "status": "telah_berakhir"
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                "status": 404,
                "message": "Tidak ada event yang ditemukan",
                "data": {
                    "event_exists": False
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        active_event = active_events.first()
        
        has_submitted = PilihanSiswa.objects.filter(
            event=active_event,
            student=student
        ).exists()
        
        return Response({
            "status": 200,
            "message": "Event aktif ditemukan",
            "data": {
                "event_exists": True,
                "is_active": True,
                "event_id": active_event.id,
                "start_date": active_event.start_date,
                "end_date": active_event.end_date,
                "has_submitted": has_submitted,
                "status": "aktif"
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status": 500,
            "message": "Terjadi kesalahan",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_events(request):
    print("🔹 get all events")
    try:
        events = Event.objects.all().order_by('-start_date')
        
        events_data = []
        for event in events:
            # Get count of students who have submitted choices for this event
            submissions_count = PilihanSiswa.objects.filter(event=event).count()
            
            event_data = {
                "id": event.id,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "angkatan": event.angkatan.angkatan if event.angkatan else None,
                "created_at": event.createdAt,
                "updated_at": event.updatedAt,
                "submissions_count": submissions_count,
                "matpel": {
                    "tier1_option1": {
                        "id": event.tier1_option1.id if event.tier1_option1 else None,
                        "nama": event.tier1_option1.nama if event.tier1_option1 else None,
                        "capacity": event.t1o1_capacity
                    },
                    "tier1_option2": {
                        "id": event.tier1_option2.id if event.tier1_option2 else None,
                        "nama": event.tier1_option2.nama if event.tier1_option2 else None,
                        "capacity": event.t1o2_capacity
                    },
                    "tier2_option1": {
                        "id": event.tier2_option1.id if event.tier2_option1 else None,
                        "nama": event.tier2_option1.nama if event.tier2_option1 else None,
                        "capacity": event.t2o1_capacity
                    },
                    "tier2_option2": {
                        "id": event.tier2_option2.id if event.tier2_option2 else None,
                        "nama": event.tier2_option2.nama if event.tier2_option2 else None,
                        "capacity": event.t2o2_capacity
                    },
                    "tier3_option1": {
                        "id": event.tier3_option1.id if event.tier3_option1 else None,
                        "nama": event.tier3_option1.nama if event.tier3_option1 else None,
                        "capacity": event.t3o1_capacity
                    },
                    "tier3_option2": {
                        "id": event.tier3_option2.id if event.tier3_option2 else None,
                        "nama": event.tier3_option2.nama if event.tier3_option2 else None,
                        "capacity": event.t3o2_capacity
                    },
                    "tier4_option1": {
                        "id": event.tier4_option1.id if event.tier4_option1 else None,
                        "nama": event.tier4_option1.nama if event.tier4_option1 else None,
                        "capacity": event.t4o1_capacity
                    },
                    "tier4_option2": {
                        "id": event.tier4_option2.id if event.tier4_option2 else None,
                        "nama": event.tier4_option2.nama if event.tier4_option2 else None,
                        "capacity": event.t4o2_capacity
                    }
                }
            }
            
            # Add status based on current date
            current_date = timezone.now().date()
            if current_date < event.start_date:
                event_data["status"] = "akan_datang"
            elif current_date <= event.end_date:
                event_data["status"] = "aktif"
            else:
                event_data["status"] = "telah_berakhir"
                
            events_data.append(event_data)
        
        return Response({
            "status": 200,
            "message": "Daftar event berhasil diambil",
            "data": events_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status": 500,
            "message": "Terjadi kesalahan",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_semua_detail_pilihan_siswa(request, pk):
    LinimasaObj = Event.objects.get(id=pk)

    PilihanSiswaObj = PilihanSiswa.objects.filter(event=LinimasaObj)
    data_pilihan = []
    data_matkul = []
    for i in PilihanSiswaObj:
        PilihanSiswaData = ({
            "id": i.id,
            "nama_siswa": i.student.username,
            "id_siswa": i.student.user_id,
            "tier1": i.tier1,
            "tier2": i.tier2,
            "tier3": i.tier3,
            "tier4": i.tier4,
            "statustier1": i.statustier1,
            "statustier2": i.statustier2,
            "statustier3": i.statustier3,
            "statustier4": i.statustier4,
            "submitted_at": i.submitted_at,
            "note": i.note,
            "id_event": i.event.id,
            
            # Tambahkan nama option berdasarkan relasi event
            "tier1_nama_option1": i.event.tier1_option1.nama if i.event.tier1_option1 else None,
            "tier1_nama_option2": i.event.tier1_option2.nama if i.event.tier1_option2 else None,
            "tier2_nama_option1": i.event.tier2_option1.nama if i.event.tier2_option1 else None,
            "tier2_nama_option2": i.event.tier2_option2.nama if i.event.tier2_option2 else None,
            "tier3_nama_option1": i.event.tier3_option1.nama if i.event.tier3_option1 else None,
            "tier3_nama_option2": i.event.tier3_option2.nama if i.event.tier3_option2 else None,
            "tier4_nama_option1": i.event.tier4_option1.nama if i.event.tier4_option1 else None,
            "tier4_nama_option2": i.event.tier4_option2.nama if i.event.tier4_option2 else None,
        })
        data_pilihan.append(PilihanSiswaData)
    return Response({
            "status": 200,
            "message": "List Submisi Siswa berhasil didapatkan",
            "data": data_pilihan
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_detail_pilihan_siswa(request):
    data = request.data
    submisi_id = data.get('submisiId')
    LinimasaObj = Event.objects.get(id=submisi_id)

    PilihanSiswaObj = PilihanSiswa.objects.filter(Event=LinimasaObj)
    data_pilihan = []
    for i in PilihanSiswaObj:
        PilihanSiswaData = ({
            "id": i.id,
            "nama_siswa": i.student.username,
            "id_siswa": i.student.user_id,
            "tier1": i.tier1,
            "tier2": i.tier2,
            "tier3": i.tier3,
            "tier4": i.tier4,
            "statustier1": i.statustier1,
            "statustier2": i.statustier2,
            "statustier3": i.statustier3,
            "statustier4": i.statustier4,
            "submitted_at": i.submitted_at,
            "note": i.note,
            
            # Tambahkan nama option berdasarkan relasi event
            "tier1_nama_option1": i.event.tier1_option1.nama if i.event.tier1_option1 else None,
            "tier1_nama_option2": i.event.tier1_option2.nama if i.event.tier1_option2 else None,
            "tier2_nama_option1": i.event.tier2_option1.nama if i.event.tier2_option1 else None,
            "tier2_nama_option2": i.event.tier2_option2.nama if i.event.tier2_option2 else None,
            "tier3_nama_option1": i.event.tier3_option1.nama if i.event.tier3_option1 else None,
            "tier3_nama_option2": i.event.tier3_option2.nama if i.event.tier3_option2 else None,
            "tier4_nama_option1": i.event.tier4_option1.nama if i.event.tier4_option1 else None,
            "tier4_nama_option2": i.event.tier4_option2.nama if i.event.tier4_option2 else None,

            "tier1_capacity_option1": i.event.t1o1_capacity,
            "tier1_capacity_option2": i.event.t1o2_capacity,
            "tier2_capacity_option1": i.event.t2o1_capacity,
            "tier2_capacity_option2": i.event.t2o2_capacity,
            "tier3_capacity_option1": i.event.t3o1_capacity,
            "tier3_capacity_option2": i.event.t3o2_capacity,
            "tier4_capacity_option1": i.event.t4o1_capacity,
            "tier4_capacity_option2": i.event.t4o2_capacity,

        })
        data_pilihan.append(PilihanSiswaData)
    return Response({
            "status": 200,
            "message": "List Submisi Siswa berhasil didapatkan",
            "data": data_pilihan
        }, status=status.HTTP_200_OK)
    

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_pilihan_status(request):
    print("🔹 update pilihan status - accept/reject")
    try:
        data = request.data
        pilihan_id = data.get('pilihan_id')
        if not pilihan_id:
            return Response({
                "status": 400,
                "message": "Data tidak lengkap",
                "error": "pilihan_id wajib diisi"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            pilihan_siswa = PilihanSiswa.objects.get(id=pilihan_id)
        except PilihanSiswa.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Pilihan siswa tidak ditemukan",
                "error": f"PilihanSiswa dengan ID {pilihan_id} tidak ditemukan"
            }, status=status.HTTP_404_NOT_FOUND)

        student = pilihan_siswa.student
        event = pilihan_siswa.event
        updated_fields = []
        enrollment_results = []

        def process_tier(tier_key):
            status_key = f"{tier_key}"
            nilai_status = data.get(status_key)
            if nilai_status is None:
                return

            # Update status di model
            setattr(pilihan_siswa, f"status{status_key}", bool(nilai_status))
            updated_fields.append(status_key)

            # Ambil pilihan lama
            pilihan_bool = getattr(pilihan_siswa, tier_key)
            option1 = getattr(event, f"{tier_key}_option1")
            option2 = getattr(event, f"{tier_key}_option2")

            matpel_lama = option1 if pilihan_bool == False else option2

            for m in [option1, option2]:
                if m and m.siswa_terdaftar.filter(user_id=student.user_id).exists():
                    m.siswa_terdaftar.remove(student)

            # Tentukan matpel baru
            if bool(nilai_status):
                matpel_baru = matpel_lama  # Diterima → pilihan awal siswa
                status_text = "Diterima"
            else:
                matpel_baru = option2 if pilihan_bool == False else option1  # Ditolak → pilihan alternatif
                status_text = "Ditolak"

            if matpel_baru:
                matpel_baru.siswa_terdaftar.add(student)
                enrollment_results.append({
                    "tier": tier_key,
                    "status": status_text,
                    "enrolled_in": {
                        "id": matpel_baru.id,
                        "nama": matpel_baru.nama
                    }
                })

        # Jalankan untuk tiap tier
        for tier in ['tier1', 'tier2', 'tier3', 'tier4']:
            process_tier(tier)

        # Simpan catatan dari wali kelas
        note = data.get("note")
        if note is not None:
            pilihan_siswa.note = note

        # Save changes
        if updated_fields:
            pilihan_siswa.save()
            return Response({
                "status": 200,
                "message": "Status pilihan siswa berhasil diupdate",
                "data": {
                    "id": pilihan_siswa.id,
                    "student_id": student.user_id,
                    "student_name": student.username,
                    "updated_fields": updated_fields,
                    "enrollment_results": enrollment_results,
                    "note": pilihan_siswa.note,
                    "status": {
                        "tier1": pilihan_siswa.statustier1,
                        "tier2": pilihan_siswa.statustier2,
                        "tier3": pilihan_siswa.statustier3,
                        "tier4": pilihan_siswa.statustier4
                    }
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": 400,
                "message": "Tidak ada perubahan",
                "error": "Setidaknya satu status tier harus diupdate"
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": 500,
            "message": "Terjadi kesalahan",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_angkatan(request):
    all_angkatan = Angkatan.objects.all()
    data_angkatan = []
    for i in all_angkatan:
        data_angkatan_temp = {
            "id":i.id,
            "angkatan":i.angkatan
        }
        data_angkatan.append(data_angkatan_temp)
    return Response({
            "status": 200,
            "message": "Data Angkatan",
            "data": data_angkatan
        }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_linimasa(request,pk):
    event = Event.objects.get(id=pk)
    event.delete()
    return Response({
            "status": 200,
            "message": "Data Angkatan",
            "data": "Linimasa berhasil dihapus"
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_tahun_ajaran(request):
    all_angkatan = TahunAjaran.objects.all()
    data_angkatan = []
    for i in all_angkatan:
        data_angkatan_temp = {
            "id":i.id,
            "tahunAjaran":i.tahunAjaran
        }
        data_angkatan.append(data_angkatan_temp)
    return Response({
            "status": 200,
            "message": "Data Angkatan",
            "data": data_angkatan
        }, status=status.HTTP_200_OK)
        