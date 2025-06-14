from django.urls import path
from . import views # Mengimpor views dari aplikasi yang sama (evalguru)

# Aplikasi ini akan di-include dengan prefix 'api/evalguru/' dari urls.py proyek utama
urlpatterns = [
    # Endpoint untuk siswa mengisi evaluasi guru
    # URL menjadi: api/evalguru/isi/
    path('isi/', views.siswafill_evalguru, name='siswa_fill_evalguru'),

    # Endpoint untuk guru melihat detail evaluasi dalam satu mata pelajaran
    # URL menjadi: api/evalguru/detail-mapel/
    # Direkomendasikan menggunakan query params untuk GET: ?guru_id=X&matapelajaran_id=Y
    path('detail-mapel/', views.guru_get_evalguru_in_mapel, name='guru_get_evalguru_in_mapel'),

    # Endpoint untuk guru melihat rangkuman evaluasi semua mata pelajaran yang diajarnya
    # URL menjadi: api/evalguru/rangkuman-guru/
    # Direkomendasikan menggunakan query params untuk GET: ?guru_id=X
    path('rangkuman-guru/', views.guru_get_all_evaluations_summary, name='guru_get_all_evaluations_summary'),

    # Endpoint untuk melihat rangkuman evaluasi keseluruhan guru per tahun ajaran (untuk admin)
    # URL menjadi: api/evalguru/overview-tahunan/
    # Menggunakan GET, tidak ada parameter yang dibutuhkan dari client via URL path atau query
    path('overview-tahunan/', views.get_overall_teacher_evaluations_overview, name='get_overall_teacher_evaluations_overview'),

    # Endpoint untuk melihat detail evaluasi guru per tahun ajaran (untuk admin)
    # URL menjadi: api/evalguru/detail-tahunan/
    # Direkomendasikan menggunakan query params untuk GET: ?guru_id=X&tahun_ajaran_id=Y
    path('detail-tahunan/', views.get_teacher_evaluation_detail_page, name='get_teacher_evaluation_detail_page'),


    path('create/', views.create_evalguru, name='create_evalguru'),
    path('cek/<int:pk>/', views.get_cek_kelas, name='get_cek_kelas'),
    path('matpel/<int:pk>/', views.get_evaluasi_guru, name='get_evalguru'),
    path('permatpel/', views.get_evaluasi_guru_per_matpel, name='get_evalguru_detail'),
]