# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/users/views.py
# Contiene: FT-23 (RegisterView) FT-24 (LoginView)
#           FT-23 (LogoutView)   FT-25 (ProfileView)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-23 — RegisterView
# POST /api/v1/auth/register/
# No requiere token → AllowAny
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'Usuario creado exitosamente.',
                    'user': UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-24 — LoginView
# POST /api/v1/auth/login/
# No requiere token → AllowAny
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-23 — LogoutView
# POST /api/v1/auth/logout/
# Requiere token → IsAuthenticated
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Sesión cerrada exitosamente.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-25 — ProfileView
# Extiende RetrieveUpdateAPIView
# GET   → ProfileSerializer (lectura completa)
# PATCH → ProfileUpdateSerializer (solo display_name/avatar/timezone)
# GET+PATCH /api/v1/auth/profile/
# Requiere token → IsAuthenticated
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']  # desactiva PUT

    def get_object(self):
        # Devuelve el Profile del usuario autenticado
        # sin necesidad de ID en la URL
        return self.request.user.profile

    def get_serializer_class(self):
        # GET   → ProfileSerializer
        # PATCH → ProfileUpdateSerializer
        if self.request.method == 'PATCH':
            return ProfileUpdateSerializer
        return ProfileSerializer
    
    