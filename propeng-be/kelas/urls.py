from django.urls import path
from kelas.views import list_kelas, create_kelas, detail_kelas, delete_kelas, update_kelas

urlpatterns = [
    path('create/', create_kelas, name='create_kelas'),
    path('<int:kelas_id>/', detail_kelas, name='detail_kelas'),
    path('delete/<int:kelas_id>', delete_kelas, name='delete_kelas'),
    path('update/<int:kelas_id>', update_kelas, name='update_kelas'),
]
