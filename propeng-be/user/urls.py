from django.urls import path
from .views import LoginView, RefreshTokenView, protected_view, logout_view
urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('protected/', protected_view, name='protected'),
    path('logout/', logout_view, name='logout'),
]
