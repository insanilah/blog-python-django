from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from utils import response
from django.shortcuts import redirect
import requests
from django.http import JsonResponse
from django.contrib.auth.models import User  # Untuk bekerja dengan model User
from rest_framework_simplejwt.tokens import RefreshToken  
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import json
from django.http import JsonResponse

User = get_user_model()

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            return response.api_response(
                code=200,
                message="success",
                status=status.HTTP_201_CREATED   
            )
            
        return response.api_response(
                code=400,
                message="bad request",
                data=[],
                status=status.HTTP_400_BAD_REQUEST   
            )

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            # Validasi kredensial menggunakan serializer
            serializer.is_valid(raise_exception=True)
            # Jika valid, ambil token dari serializer
            tokens = serializer.validated_data
            return response.api_response(
                code=200,
                message="success",
                data={"token": tokens["access"]},
                error="",
                status=status.HTTP_200_OK)
            
        except AuthenticationFailed as e:
            # Tangkap error saat login gagal
            return response.api_response(
                code=400,
                message="bad request",
                data=[],
                error=str(e.detail),
                status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Tangkap semua error lainnya
            return response.api_response(
                code=400,
                message="bad request",
                data=[],
                error=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def google_login(request):
    # Mengarahkan ke URL login Google
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    client_id = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
    redirect_uri = "http://localhost:8000/auth/google/callback"
    scope = "openid email profile"
    response_type = "code"

    auth_url = f"{google_auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}"
    print(auth_url)
    return redirect(auth_url)

def google_callback(request):
    # Dapatkan kode otorisasi dari URL query parameters
    code = request.GET.get('code')

    if not code:
        return JsonResponse({'error': 'Authorization code missing'}, status=400)

    # Tukar kode otorisasi dengan access token
    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'code': code,
        'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
        'redirect_uri': 'http://localhost:8000/auth/google/callback',
        'grant_type': 'authorization_code',
    }
    response = requests.post(token_url, data=data)

    print(response.json())
    if response.status_code != 200:
        return JsonResponse({'error': 'Failed to obtain access token'}, status=400)

    tokens = response.json()
    access_token = tokens.get('access_token')

    # Gunakan access_token untuk mendapatkan info pengguna dari Google
    user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    user_info = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'}).json()

    # Buat atau dapatkan pengguna di sistem Anda
    user, created = User.objects.get_or_create(
        username=user_info['email'],
        defaults={'first_name': user_info.get('given_name', ''), 'last_name': user_info.get('family_name', '')}
    )

    # Buat JWT token untuk pengguna dan kirimkan sebagai respons
    refresh = RefreshToken.for_user(user)
    return JsonResponse({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })

def refresh_token(request):
    print("Request:", request)
    
    if request.method == 'POST':
        try:
            body = json.loads(request.body)  # Parsing JSON dari body request
            refresh_token = body.get('refresh_token')
            if not refresh_token:
                return JsonResponse({"error": "refresh_token is required"}, status=400)
                
            url = "https://oauth2.googleapis.com/token"
            data = {
                'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            }

            print("Data dikirim ke Google:", data)
            # Kirim POST request ke Google
            response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            print("Response dari Google:", response.status_code, response.text)
            
            if response.status_code == 200:
                access_token = response.json().get('access_token')
                return JsonResponse({
                    'access': str(access_token),
                })
            else:
                return JsonResponse({
                    'error': "Failed to refresh token",
                    'details': response.json(),
                })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
