from django.urls import path
from contoh_app_propeng import views

urlpatterns = [
    path("", views.home, name="home"),
]