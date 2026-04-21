# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/workouts/serializers.py
# Contiene: FT-43 (WorkoutSerializer)
#           FT-44 (WorkoutExerciseSerializer)
#           FT-45 (ExerciseSetSerializer)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import serializers
from .models import Workout, WorkoutExercise, ExerciseSet


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-45 — ExerciseSetSerializer
# Serializa una serie de ejercicio
# reps mínimo 1 → criterio FT-41
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = [
            'id',
            'set_number',
            'reps',
            'weight_kg',
            'completed',
        ]
        read_only_fields = ['id']

    def validate_reps(self, value):
        # reps mínimo 1 → criterio FT-41
        if value < 1:
            raise serializers.ValidationError('Las repeticiones deben ser al menos 1.')
        return value


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-44 — WorkoutExerciseSerializer
# Serializa un ejercicio dentro del workout
# con sus series anidadas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class WorkoutExerciseSerializer(serializers.ModelSerializer):
    sets = ExerciseSetSerializer(many=True, read_only=True)
    exercise_name = serializers.CharField(
        source='exercise.name',
        read_only=True
    )
    exercise_category = serializers.CharField(
        source='exercise.category',
        read_only=True
    )

    class Meta:
        model = WorkoutExercise
        fields = [
            'id',
            'exercise',
            'exercise_name',
            'exercise_category',
            'order',
            'notes',
            'sets',
        ]
        read_only_fields = ['id']

    def validate_exercise(self, value):
        # Verifica que el ejercicio esté activo
        if not value.is_active:
            raise serializers.ValidationError('Este ejercicio no está disponible.')
        return value


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-43 — WorkoutSerializer
# Serializa la sesión de entrenamiento
# con sus ejercicios anidados
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class WorkoutSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = [
            'id',              # ← criterio ✅ UUID devuelto en 201
            'started_at',
            'finished_at',
            'notes',
            'total_xp_gained',
            'is_completed',
            'workout_exercises',
        ]
        read_only_fields = [
            'id',
            'started_at',
            'finished_at',
            'total_xp_gained',
            'is_completed',
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-47 — WorkoutListSerializer
# Serializa lista de workouts sin ejercicios
# para el historial paginado
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class WorkoutListSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField()

    class Meta:
        model = Workout
        fields = [
            'id',
            'started_at',
            'finished_at',
            'total_xp_gained',
            'is_completed',
            'exercise_count',
        ]

    def get_exercise_count(self, obj):
        # Cuenta cuántos ejercicios tiene el workout
        return obj.workout_exercises.count()