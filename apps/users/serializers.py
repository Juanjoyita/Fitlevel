# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/users/serializers.py
# Contiene: FT-23 (Register) FT-24 (CustomToken)
#           FT-25 (ProfileUpdate)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Profile


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-23 — RegisterSerializer
# Valida y crea un nuevo usuario
# POST /api/v1/auth/register/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este username ya está en uso.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return data

    def create(self, validated_data):
        # Elimina password2 antes de crear el user
        # create_user() hashea la contraseña automáticamente
        # El signal post_save crea el Profile automáticamente (FT-20)
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
        )
        return user


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-23 — ProfileSerializer
# Serializa el perfil RPG completo
# Usado en GET /api/v1/auth/profile/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'display_name',       # editable
            'avatar',             # editable
            'total_xp',           # solo lectura → gamificación
            'current_level',      # solo lectura → gamificación
            'current_streak',     # solo lectura → gamificación
            'longest_streak',     # solo lectura → gamificación
            'last_workout_date',  # solo lectura → gamificación
            'timezone',           # editable
        ]
        read_only_fields = [
            'total_xp',
            'current_level',
            'current_streak',
            'longest_streak',
            'last_workout_date',
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-25 — ProfileUpdateSerializer
# Solo permite modificar display_name,
# avatar y timezone
# Usado en PATCH /api/v1/auth/profile/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'display_name',   # editable → nombre visible
            'avatar',         # editable → foto de perfil
            'timezone',       # editable → zona horaria
            'total_xp',       # solo lectura → gamificación
            'current_level',  # solo lectura → gamificación
            'current_streak', # solo lectura → gamificación
        ]
        read_only_fields = [
            'total_xp',
            'current_level',
            'current_streak',
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-23 — UserSerializer
# Serializa User completo con Profile anidado
# Usado en respuesta del RegisterView
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'date_joined', 'profile']


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-24 — CustomTokenObtainPairSerializer
# Extiende login de simplejwt para incluir
# datos RPG en la respuesta
# POST /api/v1/auth/login/
# Registrado en SIMPLE_JWT → TOKEN_OBTAIN_SERIALIZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def get_rpg_title(self, level):
        # Título RPG según nivel general del usuario
        if level <= 2:
            return 'Novato'
        elif level <= 5:
            return 'Atleta'
        elif level <= 10:
            return 'Guerrero'
        elif level <= 20:
            return 'Campeón'
        else:
            return 'Leyenda'

    def validate(self, attrs):
        # super().validate() verifica email+password
        # y genera access + refresh tokens
        data = super().validate(attrs)

        profile = self.user.profile  # via related_name='profile' (FT-19)

        # Agrega datos RPG en la respuesta del login
        # Flutter recibe tokens + datos RPG en una sola llamada
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'display_name': profile.display_name,
            'title': self.get_rpg_title(profile.current_level),
            'current_level': profile.current_level,
            'total_xp': profile.total_xp,
            'current_streak': profile.current_streak,
        }
        return data