from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user

class GoogleLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def validate(self, data):
        access_token = data.get('access_token')
        if not access_token:
            raise serializers.ValidationError('Access token is required.')

        # Verifikasi dan ambil data pengguna dari Google
        user_info = self.get_google_user_info(access_token)
        if not user_info:
            raise serializers.ValidationError('Invalid token.')

        # Ambil atau buat pengguna
        user, created = User.objects.get_or_create(
            username=user_info['email'],  # Atau gunakan field lain dari data Google
            defaults={'first_name': user_info.get('given_name', ''), 'last_name': user_info.get('family_name', '')}
        )

        # Buat token JWT
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def get_google_user_info(self, token):
        import requests
        url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
