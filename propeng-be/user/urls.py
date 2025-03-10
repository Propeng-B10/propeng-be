from django.urls import path
from .views import *
urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('protected/', protected_view, name='protected'),
    path('logout/', logout_view.as_view(), name='logout'),
    path('register/', RegisterUserView.as_view(), name='register-user'),
    path('list_teacher/', list_teacher, name="list_teacher"),
    path('list_active_teacher/', list_active_teacher, name="list_active_teacher"),
    path('list_student/', list_student, name="list_student"),
    path('list_active_student/', list_active_student, name="list_active_student"),
    path('profile/<int:id>/', profile, name="profile")
]