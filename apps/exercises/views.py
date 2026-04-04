# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/exercises/views.py
# Contiene: FT-36 (ExerciseListView, ExerciseDetailView)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Exercise
from .serializers import ExerciseListSerializer, ExerciseDetailSerializer


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-36 — ExerciseListView
# Extiende ListAPIView → criterio ✅
# GET /api/v1/exercises/
#
# Filtros disponibles:
# ?muscle=chest    → ejercicios de fuerza por músculo
# ?category=cardio → ejercicios de cardio
# Sin parámetros   → todos los ejercicios activos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseListSerializer

    def get_queryset(self):
        # Base: solo ejercicios activos → criterio ✅
        # prefetch_related → evita N+1 → criterio ✅
        # exercise_muscles__muscle_group carga en una sola query
        queryset = Exercise.objects.filter(
            is_active=True
        ).prefetch_related(
            'exercise_muscles__muscle_group'
        )

        # Filtro por categoría → ?category=cardio o ?category=strength
        # Permite a Flutter mostrar sección separada de cardio
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filtro por músculo → ?muscle=chest → criterio ✅
        # Filtra ejercicios que tienen ese slug en sus músculos
        # Solo aplica a ejercicios de fuerza (cardio no tiene músculos)
        muscle = self.request.query_params.get('muscle')
        if muscle:
            queryset = queryset.filter(
                exercise_muscles__muscle_group__slug=muscle
            ).distinct()  # distinct() evita duplicados si hay varios músculos

        return queryset


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-36 — ExerciseDetailView
# Devuelve detalle completo de un ejercicio
# con todos sus músculos y multiplicadores
# GET /api/v1/exercises/{id}/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseDetailSerializer

    def get_queryset(self):
        return Exercise.objects.filter(
            is_active=True
        ).prefetch_related(
            'exercise_muscles__muscle_group'
        )