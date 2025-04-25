# capaiankompetensi/urls.py

from django.urls import path
from . import views

# Nama namespace, opsional tapi bagus untuk organisasi jika proyek besar
app_name = 'capaiankompetensi'

urlpatterns = [
    # Hanya satu URL pattern yang kita perlukan sekarang:
    # Menangani GET (ambil kedua deskripsi) dan POST (update/create deskripsi)
    # untuk Capaian Kompetensi berdasarkan ID Mata Pelajaran (<mapel_pk>)
    path(
        # Pola URL: diawali 'api/', diikuti 'capaiankompetensi/', lalu ID mapel integer
        '<int:mapel_pk>/',
         views.capaian_api_view,
         name='api_capaian'
    ),
    path(
        'subject/<int:matapelajaran_id>/descriptions/', # Clearer path
         views.get_capaian_descriptions_for_subject,
         name='get_capaian_descriptions' # Unique name
    ),
]