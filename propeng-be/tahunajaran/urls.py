from django.urls import path
from .views import list_angkatan

urlpatterns = [
    path('list_angkatan/', list_angkatan, name='list_angkatan'),
]
