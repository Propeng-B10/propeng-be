from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_mata_pelajaran, name='create_mata_pelajaran'),
    path('update/<int:pk>/', update_mata_pelajaran, name='update_mata_pelajaran'),
    path('delete/<int:pk>/', delete_mata_pelajaran, name='delete_mata_pelajaran'),
    path('list/', list_matapelajaran, name='list-matapelajaran'),
    path('archive/<int:pk>/', archive_mata_pelajaran, name='archive_mata_pelajaran'),
]