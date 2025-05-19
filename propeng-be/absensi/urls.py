from django.urls import path
from absensi.views import *
urlpatterns = [
    path('', list_all_absen, name='list_kelas'),
    path('absen-submit/', absen, name='absensi_siswa'),
    path('kelas/<int:kelas_id>/', absensi_kelas_table, name='absensi_kelas_table'),
    path('update-status/', update_student_absensi, name='update_student_absensi'),
    path('student/summary/', get_student_attendance_summary, name='get_student_attendance_summary'),
    path('kelas/<int:kelas_id>/weekly-summary/', get_weekly_attendance_summary_details, name='weekly_attendance_summary_details'),
    path('kelas/<int:kelas_id>/monthly-analysis/', get_monthly_student_attendance_analysis, name='monthly_attendance_analysis'),
    path('kelas/<int:kelas_id>/monthly-detail/', get_monthly_student_attendance_detail, name='monthly_student_attendance_detail'),
    path('kelas/<int:kelas_id>/monthly-overview/', get_monthly_class_attendance_overview, name='monthly_class_attendance_overview'),
    path('kelas/<int:kelas_id>/yearly-summary/', get_yearly_attendance_summary, name='yearly_attendance_summary'),
]
