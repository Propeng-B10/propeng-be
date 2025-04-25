from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_nilai, name='create_nilai'),
    path('matapelajaran/<int:matapelajaran_id>/', views.get_nilai_by_matapelajaran, name='get_nilai_by_matapelajaran'),
    path('student/<int:student_id>/', views.get_nilai_by_student, name='get_nilai_by_student'),
    path('update/<int:nilai_id>/', views.update_nilai, name='update_nilai'),
    path('subjects/<int:matapelajaran_id>/gradedata/',
         views.grade_data_view,
         name='grade_data_detail'),
    path('subjects/',
         views.get_teacher_subjects_summary,
         name='teacher_subject_summary_list'),
    path('student/my-grades/', views.get_student_all_grades, name='get_student_all_grades'),

] 