# absensi/utils.py

import calendar
from django.utils import timezone
from datetime import date, timedelta
import random
import string
import json
import traceback
from collections import defaultdict
from django.apps import apps

def populate_dummy_attendance_for_class(class_name, start_date, end_date, attendance_weights=None):
    """
    Populates dummy attendance records for a specific class within a date range.
    Skips weekends and dates with existing records.
    Expects class_name as string, start_date/end_date as date objects.
    attendance_weights is an optional dict like {'Hadir': 0.8, ...}
    """
    try:
        Kelas = apps.get_model('kelas', 'Kelas')
        AbsensiHarian = apps.get_model('absensi', 'AbsensiHarian')
        Student = apps.get_model('user', 'Student')
    except LookupError:
        print("Warning: Models not ready for attendance population utility.")
        return

    default_attendance_weights = {'Hadir': 0.80, 'Sakit': 0.05, 'Izin': 0.05, 'Alfa': 0.10}
    weights = attendance_weights if attendance_weights is not None else default_attendance_weights
    attendance_statuses = list(weights.keys())

    print(f"\nAttempting to populate attendance for class '{class_name}' from {start_date} to {end_date}...")
    try:
        kelas_obj = Kelas.objects.filter(namaKelas__iexact=class_name).first()

        if not kelas_obj:
            print(f"Skipping attendance population: Class '{class_name}' not found. Ensure it's created by another process.")
            return

        students_in_class_pks = list(kelas_obj.siswa.values_list('pk', flat=True))
        if not students_in_class_pks:
             print(f"Skipping attendance population: No students found in class '{kelas_obj.namaKelas}'.")
             return

        students_lookup = {student.user_id: student for student in Student.objects.filter(pk__in=students_in_class_pks)}

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5: # Skip weekends
                current_date += timedelta(days=1)
                continue

            existing_absensi = AbsensiHarian.objects.filter(
                kelas=kelas_obj,
                date=current_date
            ).first()

            if existing_absensi:
                pass
            else:
                absensi_record = AbsensiHarian(
                    kelas=kelas_obj,
                    date=current_date,
                    tipeAbsensi='Absen'
                )
                absensi_record.save()

                updated_list_siswa = {}
                for student_user_id_int in students_in_class_pks:
                     student_id_str = str(student_user_id_int)
                     random_status = random.choices(attendance_statuses, weights=list(weights.values()), k=1)[0]

                     student_obj = students_lookup.get(student_user_id_int)
                     student_name = student_obj.name if student_obj else f"Student {student_user_id_int}"

                     updated_list_siswa[student_id_str] = {
                         "name": student_name,
                         "status": random_status,
                         "id": student_user_id_int
                     }

                absensi_record.listSiswa = updated_list_siswa
                absensi_record.save()

            # --- FIX: Use current_date here, not current_day ---
            current_date += timedelta(days=1)

        print(f"Finished attendance population for class '{kelas_obj.namaKelas}' from {start_date} to {end_date}.")

    except Exception as e:
        print(f"An error occurred during attendance population for class '{class_name}': {e}")
        traceback.print_exc()

# --- Add other utility functions here if needed ---

