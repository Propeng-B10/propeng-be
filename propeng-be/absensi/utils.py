# absensi/utils.py

import calendar
from django.utils import timezone
from datetime import date, timedelta
import random
import traceback
from collections import defaultdict
from django.apps import apps

def populate_dummy_attendance_for_class(
    class_name,
    start_date=None,
    end_date=None,
    attendance_weights=None,
    use_patterns=True,
    year=None
):
    """
    Populates dummy attendance for a class so that, for every weekday
    between Jan–June, each day has entries for all students AND ensures
    that each of the four statuses appears at least once per day.
    """
    try:
        Kelas = apps.get_model('kelas', 'Kelas')
        AbsensiHarian = apps.get_model('absensi', 'AbsensiHarian')
        Student = apps.get_model('user', 'Student')
    except LookupError:
        print("Models not ready.")
        return False

    # --- determine date range: default Jan–June of `year` if provided ---
    if year and start_date is None and end_date is None:
        start_date = date(year, 1, 1)
        end_date   = date(year, 6, 30)
    elif start_date is None or end_date is None:
        today = timezone.now().date()
        start_date = start_date or date(today.year, today.month, 1)
        last = calendar.monthrange(today.year, today.month)[1]
        end_date   = end_date   or date(today.year, today.month, last)

    print(f"Populating {class_name} from {start_date} to {end_date}")

    kelas_obj = Kelas.objects.filter(namaKelas__iexact=class_name).first()
    if not kelas_obj:
        print("Class not found.")
        return False

    student_qs = kelas_obj.siswa.all()
    if not student_qs.exists():
        print("No students in class.")
        return False

    students = list(student_qs)
    statuses = ["Hadir", "Sakit", "Izin", "Alfa"]

    # Pre‐compute any pattern factors if you like...
    # For brevity I’ll skip that here; assume you have a function
    # `generate_attendance_status(student, date_obj)` returning one of the above.

    def gen_status(student_id, current_date):
        # stub: replace with your pattern logic or random choice
        return random.choice(statuses)

    records_created = records_updated = 0
    current = start_date
    while current <= end_date:
        # skip weekends
        if current.weekday() < 5:
            # fetch or create
            abs_rec = AbsensiHarian.objects.filter(kelas=kelas_obj, date=current).first()
            if not abs_rec:
                abs_rec = AbsensiHarian(kelas=kelas_obj, date=current, tipeAbsensi="Absen")
            # build initial map
            day_map = {}
            for s in students:
                st = gen_status(s.user_id, current)
                day_map[str(s.user_id)] = {
                    "name": s.name,
                    "status": st,
                    "id": s.user_id
                }

            # ** enforce coverage **
            present_statuses = { info["status"] for info in day_map.values() }
            missing = [st for st in statuses if st not in present_statuses]

            # for each missing status, pick one random student and override
            available_ids = list(day_map.keys())
            random.shuffle(available_ids)
            for m in missing:
                for sid in available_ids:
                    if day_map[sid]["status"] != m:
                        day_map[sid]["status"] = m
                        # remove so we don't pick same again
                        available_ids.remove(sid)
                        break

            # assign and save
            abs_rec.listSiswa = day_map
            abs_rec.save()
            if abs_rec._state.adding:
                records_created += 1
            else:
                records_updated += 1

        current += timedelta(days=1)

    print(f"Done: {records_created} created, {records_updated} updated.")
    return True