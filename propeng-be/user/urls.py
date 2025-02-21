from django.urls import path
from .views import LoginView, RefreshTokenView, protected_view

urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('protected/', protected_view, name='protected'),
]
