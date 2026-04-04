# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/exercises/serializers.py
# Contiene: FT-36 (ExerciseListSerializer)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import serializers
from .models import Exercise, MuscleGroup


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-36 — MuscleGroupSerializer
# Serializa un grupo muscular básico
# Usado como campo anidado en Exercise
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = ['id', 'name', 'slug', 'body_zone', 'svg_element_id']


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-36 — ExerciseListSerializer
# Serializa ejercicio con su músculo primario
# Campos requeridos por criterio:
# id, name, difficulty, base_xp, primary_muscle
# También incluye category para distinguir
# ejercicios de fuerza y cardio
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseListSerializer(serializers.ModelSerializer):
    # primary_muscle → músculo principal del ejercicio
    # SerializerMethodField → campo calculado, no viene del modelo directamente
    primary_muscle = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id',
            'name',
            'difficulty',
            'category',       # strength o cardio
            'base_xp',
            'primary_muscle', # músculo principal (null para cardio)
        ]

    def get_primary_muscle(self, obj):
        # Busca en exercise_muscles el que tiene is_primary=True
        # prefetch_related ya cargó estos datos → sin consultas extra (N+1)
        # Los ejercicios de cardio no tienen músculos → devuelve None
        for em in obj.exercise_muscles.all():
            if em.is_primary:
                return MuscleGroupSerializer(em.muscle_group).data
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-36 — ExerciseDetailSerializer
# Serializa ejercicio completo con TODOS
# sus músculos y multiplicadores
# Usado en GET /api/v1/exercises/{id}/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseMuscleDetailSerializer(serializers.Serializer):
    # Serializa cada relación exercise-muscle con su multiplicador
    muscle = MuscleGroupSerializer(source='muscle_group')
    is_primary = serializers.BooleanField()
    xp_multiplier = serializers.DecimalField(max_digits=3, decimal_places=2)


class ExerciseDetailSerializer(serializers.ModelSerializer):
    muscles = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id',
            'name',
            'description',
            'difficulty',
            'category',
            'base_xp',
            'is_active',
            'muscles',  # lista de músculos con multiplicadores
        ]

    def get_muscles(self, obj):
        return ExerciseMuscleDetailSerializer(
            obj.exercise_muscles.all(),
            many=True
        ).data