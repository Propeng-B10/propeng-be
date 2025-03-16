from django.urls import path
from kelas.views import list_kelas, create_kelas, detail_kelas, delete_kelas, update_kelas, list_available_student_by_angkatan, list_all_homeroom, list_available_homeroom

urlpatterns = [
    path('', list_kelas, name='list_kelas'),
    path('create/', create_kelas, name='create_kelas'),
    path('<int:kelas_id>/', detail_kelas, name='detail_kelas'),
    path('delete/<int:kelas_id>/', delete_kelas, name='delete_kelas'),
    path('update/<int:kelas_id>/', update_kelas, name='update_kelas'),
    path('list_available_student/<int:angkatan>/', list_available_student_by_angkatan, name='list_available_student_by_angkatan'),
    path('list_available_homeroom/', list_available_homeroom, name='list_available_homeroom'),
    path('list_all_homeroom/', list_all_homeroom, name='list_all_homeroom'),
]
