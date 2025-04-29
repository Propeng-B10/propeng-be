from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_event, name='create_event'),
    path('ubah/', update_event, name='update_event'),
    path('pilihan-siswa/create/', create_pilihan_siswa, name='create_pilihan_siswa'),
    path('pilihan-siswa/update/', update_pilihan_siswa, name='update_pilihan_siswa'),
    path('pilihan-siswa/update-status/', update_pilihan_status, name='update_pilihan_status'),
    path('active-event/', get_active_event, name='get_active_event'),
    path('submisi/<int:pk>/', get_semua_detail_pilihan_siswa, name='get_submission'),
    path('', get_all_events, name='get_all_events'),
    path('angkatan/', get_all_angkatan, name='angkatan'),
    path('tahun-ajaran/', get_all_tahun_ajaran, name="tahun_ajaran"),
    path('delete/<int:pk>', delete_linimasa, name="hapus"),
    path('<int:pk>/', get_event, name="get_event")
]