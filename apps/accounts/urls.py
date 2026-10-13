from django.urls import path
from .views import CSRFTokenView, RegisterView, LoginView, LogoutView, MeView

urlpatterns = [
    path('csrf/', CSRFTokenView.as_view(), name='auth_csrf'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('me/', MeView.as_view(), name='auth_me'),
]
