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

def populate_dummy_attendance_for_class(class_name, start_date=None, end_date=None, attendance_weights=None, use_patterns=True, year=None):
    """
    Populates dummy attendance records for a specific class within a date range.
    Skips weekends and dates with existing records.
    
    Args:
        class_name: Name of the class to generate data for
        start_date: Start date for attendance generation (if None and year provided, uses Jan 1 of year)
        end_date: End date for attendance generation (if None and year provided, uses Dec 31 of year)
        attendance_weights: Optional dict like {'Hadir': 0.8, ...} for simple random generation
        use_patterns: If True, uses realistic patterns for attendance generation
        year: Year to generate data for (only used if start_date/end_date are None)
    
    When use_patterns=True, generates data with these patterns:
    1. Day of week patterns: More absences on Mondays and Fridays
    2. Monthly patterns: Higher absence rates during certain months
    3. Seasonal patterns: Flu season, holidays, etc.
    4. Student patterns: Some students have specific attendance issues
    5. Weekly patterns: Each week has its own attendance profile
    """
    try:
        Kelas = apps.get_model('kelas', 'Kelas')
        AbsensiHarian = apps.get_model('absensi', 'AbsensiHarian')
        Student = apps.get_model('user', 'Student')
    except LookupError:
        print("Warning: Models not ready for attendance population utility.")
        return

    # If year is provided but not start/end dates, set to full year
    if year is not None and start_date is None and end_date is None:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    elif start_date is None or end_date is None:
        # Default to current month if neither year nor proper dates provided
        today = timezone.now().date()
        if start_date is None:
            start_date = date(today.year, today.month, 1)
        if end_date is None:
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = date(today.year, today.month, last_day)

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

        if use_patterns:
            # Define patterns for different time periods when using patterned generation
            
            # 1. Monthly patterns - affects overall attendance rates
            # Higher values mean more absences
            monthly_absence_factors = {
                1: 1.2,   # January - Back from holidays, some winter illnesses
                2: 1.0,   # February - Normal
                3: 0.9,   # March - Good attendance
                4: 1.1,   # April - Spring fever
                5: 1.3,   # May - End of term fatigue
                6: 1.5,   # June - Pre-summer excitement
                7: 0.5,   # July - Summer holidays (few school days)
                8: 0.5,   # August - Summer holidays (few school days)
                9: 0.8,   # September - Back to school, fresh
                10: 1.1,  # October - Fall flu season begins
                11: 1.3,  # November - Cold/flu season peak
                12: 1.4   # December - Winter holidays, illnesses
            }
            
            # 2. Day of week patterns - affects likelihood of absence
            # Higher values mean more absences
            day_of_week_factors = {
                0: 1.3,  # Monday - Weekend hangover
                1: 0.9,  # Tuesday - Good attendance
                2: 0.8,  # Wednesday - Good attendance
                3: 0.9,  # Thursday - Good attendance
                4: 1.2   # Friday - Weekend excitement
            }
            
            # 3. Student attendance profiles
            # Randomly assign profiles to students
            profile_types = [
                "excellent",    # Rarely absent
                "good",         # Occasionally absent
                "average",      # Normal absence rate
                "poor",         # Often absent
                "chronic",      # Chronically absent
                "monday_skip",  # Often absent on Mondays
                "friday_skip",  # Often absent on Fridays
                "winter_sick",  # More sick days in winter
                "spring_sick",  # More sick days in spring
            ]
            
            # Assign profiles to students
            student_profiles = {}
            for student_id in students_in_class_pks:
                profile = random.choice(profile_types)
                student_profiles[student_id] = profile
            
            # 4. Week patterns - specific weeks with events
            # Dictionary mapping (month, week_of_month) to special event names
            special_weeks = {
                (1, 1): "First week back",     # More absences
                (3, 2): "Mid-term exam week",  # Better attendance
                (5, 4): "Final exam week",     # Better attendance
                (6, 3): "Last week of term",   # Mixed attendance
                (9, 1): "First week of term",  # Good attendance
                (10, 4): "Halloween week",     # More absences near end
                (12, 3): "Holiday week"        # Many absences
            }
        else:
            # For simple random generation, use the provided weights or defaults
            default_attendance_weights = {'Hadir': 0.80, 'Sakit': 0.05, 'Izin': 0.05, 'Alfa': 0.10}
            weights = attendance_weights if attendance_weights is not None else default_attendance_weights
            attendance_statuses = list(weights.keys())
        
        # For tracking the week number within each month when using patterns
        current_month = start_date.month
        week_of_month = 1
        first_monday_of_month = None
        
        # Track how many records were created/updated
        records_created = 0
        records_updated = 0

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5:  # Skip weekends
                current_date += timedelta(days=1)
                continue
            
            # Update week tracking when using patterns
            if use_patterns:
                # Track week of month (1-based) - reset on new month
                if current_date.month != current_month:
                    current_month = current_date.month
                    week_of_month = 1
                    first_monday_of_month = None
                
                # Find the first Monday of the month
                if first_monday_of_month is None:
                    # Get the first day of this month
                    first_day = date(current_date.year, current_date.month, 1)
                    # Calculate days to first Monday
                    days_to_first_monday = (7 - first_day.weekday()) % 7
                    first_monday_of_month = first_day + timedelta(days=days_to_first_monday)
                    
                # If we've reached a new Monday and it's after the first Monday, increment week
                if current_date.weekday() == 0 and current_date > first_monday_of_month:
                    week_of_month += 1

            # Check if this day already has an attendance record
            existing_absensi = AbsensiHarian.objects.filter(
                kelas=kelas_obj,
                date=current_date
            ).first()

            if existing_absensi:
                # Update existing record
                updated_list_siswa = {}
                
                for student_id in students_in_class_pks:
                    student_id_str = str(student_id)
                    student_obj = students_lookup.get(student_id)
                    student_name = student_obj.name if student_obj else f"Student {student_id}"
                    
                    if use_patterns:
                        # Generate attendance status based on patterns
                        status = generate_attendance_status(
                            student_id, 
                            current_date,
                            student_profiles[student_id],
                            monthly_absence_factors[current_date.month],
                            day_of_week_factors[current_date.weekday()],
                            special_weeks.get((current_date.month, week_of_month))
                        )
                    else:
                        # Simple random selection
                        status = random.choices(attendance_statuses, weights=list(weights.values()), k=1)[0]
                    
                    updated_list_siswa[student_id_str] = {
                        "name": student_name,
                        "status": status,
                        "id": student_id
                    }
                
                existing_absensi.listSiswa = updated_list_siswa
                existing_absensi.save()
                records_updated += 1
            else:
                # Create new record
                absensi_record = AbsensiHarian(
                    kelas=kelas_obj,
                    date=current_date,
                    tipeAbsensi='Absen'
                )
                absensi_record.save()

                updated_list_siswa = {}
                for student_id in students_in_class_pks:
                    student_id_str = str(student_id)
                    student_obj = students_lookup.get(student_id)
                    student_name = student_obj.name if student_obj else f"Student {student_id}"
                    
                    if use_patterns:
                        # Generate attendance status based on patterns
                        status = generate_attendance_status(
                            student_id, 
                            current_date,
                            student_profiles[student_id],
                            monthly_absence_factors[current_date.month],
                            day_of_week_factors[current_date.weekday()],
                            special_weeks.get((current_date.month, week_of_month))
                        )
                    else:
                        # Simple random selection
                        status = random.choices(attendance_statuses, weights=list(weights.values()), k=1)[0]
                    
                    updated_list_siswa[student_id_str] = {
                        "name": student_name,
                        "status": status,
                        "id": student_id
                    }

                absensi_record.listSiswa = updated_list_siswa
                absensi_record.save()
                records_created += 1

            # Move to next day
            current_date += timedelta(days=1)

        print(f"Finished attendance population for class '{kelas_obj.namaKelas}':")
        print(f"- {records_created} new records created")
        print(f"- {records_updated} existing records updated")
        if start_date.month == 1 and end_date.month == 12:
            print("Attendance data now available for all months from January to December")
        return True

    except Exception as e:
        print(f"An error occurred during attendance population for class '{class_name}': {e}")
        traceback.print_exc()
        return False

def generate_attendance_status(student_id, date_obj, profile, month_factor, day_factor, special_week=None):
    """
    Generate an attendance status for a student based on various factors and patterns.
    
    Returns one of: "Hadir", "Sakit", "Izin", "Alfa"
    """
    # Base probabilities
    base_probabilities = {
        "Hadir": 0.85,
        "Sakit": 0.06,
        "Izin": 0.05,
        "Alfa": 0.04
    }
    
    # Adjust based on student profile
    profile_adjustments = {
        "excellent": {"Hadir": 1.10, "Sakit": 0.5, "Izin": 0.5, "Alfa": 0.2},
        "good": {"Hadir": 1.05, "Sakit": 0.7, "Izin": 0.7, "Alfa": 0.5},
        "average": {"Hadir": 1.00, "Sakit": 1.0, "Izin": 1.0, "Alfa": 1.0},
        "poor": {"Hadir": 0.90, "Sakit": 1.2, "Izin": 1.1, "Alfa": 1.5},
        "chronic": {"Hadir": 0.75, "Sakit": 1.5, "Izin": 1.3, "Alfa": 2.0},
        "monday_skip": {"Hadir": 1.0, "Sakit": 1.0, "Izin": 1.0, "Alfa": 1.0},  # Handled separately
        "friday_skip": {"Hadir": 1.0, "Sakit": 1.0, "Izin": 1.0, "Alfa": 1.0},  # Handled separately
        "winter_sick": {"Hadir": 1.0, "Sakit": 1.0, "Izin": 1.0, "Alfa": 1.0},  # Handled separately
        "spring_sick": {"Hadir": 1.0, "Sakit": 1.0, "Izin": 1.0, "Alfa": 1.0}   # Handled separately
    }
    
    # Special adjustments based on profile type and date
    if profile == "monday_skip" and date_obj.weekday() == 0:
        profile_adjustments[profile]["Hadir"] = 0.7
        profile_adjustments[profile]["Alfa"] = 2.0
    elif profile == "friday_skip" and date_obj.weekday() == 4:
        profile_adjustments[profile]["Hadir"] = 0.7
        profile_adjustments[profile]["Alfa"] = 2.0
    elif profile == "winter_sick" and date_obj.month in [11, 12, 1, 2]:
        profile_adjustments[profile]["Hadir"] = 0.85
        profile_adjustments[profile]["Sakit"] = 1.8
    elif profile == "spring_sick" and date_obj.month in [3, 4, 5]:
        profile_adjustments[profile]["Hadir"] = 0.85
        profile_adjustments[profile]["Sakit"] = 1.8
    
    # Apply adjustments
    adjusted_probabilities = {}
    for status, base_prob in base_probabilities.items():
        # Multiply by all relevant factors
        factor = profile_adjustments[profile][status]
        
        # Month and day effects primarily affect absence probability
        if status != "Hadir":
            factor *= month_factor * day_factor
            
            # For special weeks, further adjust
            if special_week:
                if special_week in ["First week back", "Holiday week"]:
                    # More absences
                    factor *= 1.3
                elif special_week in ["Mid-term exam week", "Final exam week"]:
                    # Better attendance during exam weeks
                    factor *= 0.7
        
        adjusted_probabilities[status] = base_prob * factor
    
    # Normalize probabilities to sum to 1
    total = sum(adjusted_probabilities.values())
    normalized_probs = {k: v/total for k, v in adjusted_probabilities.items()}
    
    # Get statuses and their probabilities
    statuses = list(normalized_probs.keys())
    probs = list(normalized_probs.values())
    
    # Choose status based on probabilities
    return random.choices(statuses, weights=probs, k=1)[0]

def clear_attendance_data(class_name, year=None):
    """
    Clear all attendance data for a class in the specified year.
    """
    if year is None:
        year = timezone.now().year
        
    try:
        Kelas = apps.get_model('kelas', 'Kelas')
        AbsensiHarian = apps.get_model('absensi', 'AbsensiHarian')
    except LookupError:
        print("Warning: Models not ready.")
        return
    
    # Get the class object
    kelas_obj = Kelas.objects.filter(namaKelas__iexact=class_name).first()
    if not kelas_obj:
        print(f"Class '{class_name}' not found.")
        return
    
    # Delete all attendance records for this class in the specified year
    count = AbsensiHarian.objects.filter(
        kelas=kelas_obj,
        date__year=year
    ).delete()[0]
    
    print(f"Deleted {count} attendance records for class '{class_name}' in {year}.")
    return count

def populate_dummy_attendance_signal_handler(sender, **kwargs):
    # ...existing code...
    
    # Change this line:
    year = 2025  # Set to match your class year instead of timezone.now().year
    start_date_attendance = date(year, 1, 1)
    end_date_attendance = date(year, 12, 31)  # Change to December 31 to get full year
    
    # ...rest of the function...

