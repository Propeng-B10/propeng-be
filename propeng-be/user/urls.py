from django.urls import path
from .views import *
urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('protected/', protected_view, name='protected'),
    path('logout/', logout_view.as_view(), name='logout'),
    path('register/', RegisterUserView.as_view(), name='register-user'),
]