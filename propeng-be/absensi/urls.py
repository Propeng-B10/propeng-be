from django.urls import path
from absensi.views import *
urlpatterns = [
    path('', list_all_absen, name='list_kelas'),
    path('absen/', absen, name='absensi_siswa'),
]
