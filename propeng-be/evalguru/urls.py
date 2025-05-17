from django.urls import path
from . import views 

urlpatterns = [
    # Endpoint untuk siswa mengisi evaluasi guru
    path('api/evaluasi/isi/', views.siswafill_evalguru, name='siswa_fill_evalguru'),

    # Endpoint untuk guru melihat detail evaluasi dalam satu mata pelajaran
    # Menggunakan GET, parameter via query string (atau body jika tetap pakai request.data)
    path('api/guru/evaluasi/mapel/', views.guru_get_evalguru_in_mapel, name='guru_get_evalguru_in_mapel'),

    # Endpoint untuk guru melihat rangkuman evaluasi semua mata pelajaran yang diajarnya
    # Menggunakan GET, parameter guru_id via query string
    path('api/guru/evaluasi/rangkuman-mapel/', views.guru_get_all_evaluations_summary, name='guru_get_all_evaluations_summary'),

    # Endpoint untuk melihat rangkuman evaluasi keseluruhan guru per tahun ajaran (untuk admin/kepsek)
    # Menggunakan GET, tidak ada parameter yang dibutuhkan dari client
    path('api/admin/evaluasi/overview-tahunan/', views.get_overall_teacher_evaluations_overview, name='get_overall_teacher_evaluations_overview'),
]