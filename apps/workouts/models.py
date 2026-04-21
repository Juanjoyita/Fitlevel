# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/workouts/models.py
# Contiene: FT-39 (Workout) FT-40 (WorkoutExercise)
#           FT-41 (ExerciseSet)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-39 — Workout
# Representa una sesión de entrenamiento
# Se crea vacía y se completa al finalizar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Workout(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workouts'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    total_xp_gained = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Workout {self.id} - {self.user.email} ({self.started_at.date()})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-40 — WorkoutExercise
# Relaciona un ejercicio con un Workout
# Un Workout puede tener múltiples
# WorkoutExercises que definen qué se entrenó
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class WorkoutExercise(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='workout_exercises'
    )
    exercise = models.ForeignKey(
        'exercises.Exercise',
        on_delete=models.PROTECT,
        related_name='workout_exercises'
    )
    order = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.exercise.name} en {self.workout.id}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-41 — ExerciseSet
# Representa una serie dentro de un ejercicio
# Solo sets con completed=True se usan
# para el cálculo de XP en Sprint 5
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseSet(models.Model):

    id = models.UUIDField(    # UUID como primary key
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    workout_exercise = models.ForeignKey(    # si se borra el WorkoutExercise se borran sus sets
        WorkoutExercise,
        on_delete=models.CASCADE,
        related_name='sets'
    )
    set_number = models.PositiveIntegerField(     # número de serie, comienza en 1
        default=1,
        validators=[MinValueValidator(1)]
    )

    # reps mínimo 1
    reps = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    weight_kg = models.DecimalField(    # null para ejercicios de peso corporal (dominadas, fondos), max_digits=6 decimal_places=2 → hasta 9999.99 kg
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    completed = models.BooleanField(default=True)    # default=True → serie completada por defecto Solo completed=True cuenta para XP (Sprint 5)
    class Meta:
        ordering = ['set_number']
    def __str__(self):
        weight = f"{self.weight_kg}kg" if self.weight_kg else "peso corporal"
        return f"Serie {self.set_number}: {self.reps} reps × {weight}"