from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_mata_pelajaran, name='create_mata_pelajaran'),
    path('update/<int:pk>/', update_mata_pelajaran, name='update_mata_pelajaran'),
    path('delete/<int:pk>/', delete_mata_pelajaran, name='delete_mata_pelajaran'),
    path('', list_matapelajaran, name='list-matapelajaran'),
    path('<int:pk>/', get_mata_pelajaran_by_id, name='get_mata_pelajaran_by_id'),
    path('by-teacher/<int:pk>/', get_mata_pelajaran_by_teacher_id, name='get_mata_pelajaran_by_teacher_id'),
    path('tahun-ajaran/<int:pk>/', list_matapelajaran_minat_by_tahunajaran, name="minat_by_tahun_ajaran")
]
# test