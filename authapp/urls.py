from django.urls import path
from .views import RegisterView, MyTokenObtainPairView
from . import views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='login'),
    path('google/', views.google_login, name='google-login'),
    path('google/callback', views.google_callback, name='google-callback'),
    path('token/refresh/', views.refresh_token, name='refresh-token'),
]
