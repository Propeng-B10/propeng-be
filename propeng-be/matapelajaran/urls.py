from django.urls import path
from .views import create_mata_pelajaran, list_mata_pelajaran, update_mata_pelajaran, delete_mata_pelajaran

urlpatterns = [
    path('create/', create_mata_pelajaran, name='create_mata_pelajaran'),
    path('', list_mata_pelajaran, name='list_mata_pelajaran'),
    path('update/<int:pk>/', update_mata_pelajaran, name='update_mata_pelajaran'),
    path('delete/<int:pk>/', delete_mata_pelajaran, name='delete_mata_pelajaran'),
]
