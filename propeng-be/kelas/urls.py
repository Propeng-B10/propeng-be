from django.urls import path
from kelas.views import *

urlpatterns = [
    path('', list_kelas, name='list_kelas'),
    path('create/', create_kelas, name='create_kelas'),
    path('<int:kelas_id>/', detail_kelas, name='detail_kelas'),
    # Make sure this path is correctly defined
    path('delete_multiple/', delete_multiple_kelas, name='delete_multiple_kelas'),
    path('delete_siswa_from_kelas/<int:kelas_id>/<int:siswa_id>/', delete_siswa_from_kelas, name='delete_siswa_from_kelas'),
    path('update/<int:kelas_id>/', update_kelas, name='update_kelas'),
    path('update_nama_kelas/<int:kelas_id>/', update_nama_kelas, name='update_nama_kelas'),
    path('update_wali_kelas/<int:kelas_id>/', update_wali_kelas, name='update_wali_kelas'),
    path('add_siswa_to_kelas/<int:kelas_id>/', add_siswa_to_kelas, name='add_siswa_to_kelas'),
    path('list_available_student/<int:angkatan>/', list_available_student_by_angkatan, name='list_available_student_by_angkatan'),
    path('list_available_homeroom/', list_available_homeroom, name='list_available_homeroom'),
    path('list_all_homeroom/', list_all_homeroom, name='list_all_homeroom'),
    path('list_avail_absensi/', get_kelas_with_absensi, name='list_all_ada_absen'),
    path('kode/<int:kelas_id>/', get_kode_absensi_kelas, name='kode_absens'),
]
