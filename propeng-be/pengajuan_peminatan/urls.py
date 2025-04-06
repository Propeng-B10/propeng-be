from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_event, name='create_event'),
    path('pilihan-siswa/create/', create_pilihan_siswa, name='create_pilihan_siswa'),
    path('pilihan-siswa/update/', update_pilihan_siswa, name='update_pilihan_siswa'),
    path('pilihan-siswa/update-status/', update_pilihan_status, name='update_pilihan_status'),
    path('active-event/', get_active_event, name='get_active_event'),
    path('', get_all_events, name='get_all_events'),
]