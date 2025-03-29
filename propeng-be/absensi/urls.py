from django.urls import path
from absensi.views import *
urlpatterns = [
    path('', list_all_absen, name='list_kelas'),
    path('absen-submit/', absen, name='absensi_siswa'),
    path('kelas/<int:kelas_id>/', absensi_kelas_table, name='absensi_kelas_table'),
    path('update-status/', update_student_absensi, name='update_student_absensi'),
]
