from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_komponen_penilaian, name='create_komponen_penilaian'),
    path('', get_all_komponen_penilaian, name='get_all_komponen_penilaian'),
    path('by-matpel/<int:pk>/', get_komponen_penilaian_of_mata_pelajaran, name='get_komponen_penilaian_of_mata_pelajaran'),
    path('by-id/<int:pk>/', get_komponen_penilaian_by_id, name='get_komponen_penilaian_by_id'),
    path('update/<int:pk>/', update_komponen_penilaian, name='update_komponen_penilaian'),
    path('delete/<int:pk>/', delete_komponen_penilaian, name='delete_komponen_penilaian'),
]