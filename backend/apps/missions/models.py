# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/missions/models.py
# Contiene: FT-57 (Mission) FT-58 (UserMission)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
from django.conf import settings
from django.db import models


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-57 — Mission
# Define una mision con su condicion
# y recompensa de XP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Mission(models.Model):

    MISSION_TYPE_CHOICES = [
        ('daily', 'Diaria'),
        ('weekly', 'Semanal'),
    ]

    CONDITION_TYPE_CHOICES = [
        ('workout_count', 'Sesiones completadas'),
        ('xp_gained', 'XP acumulada en el dia'),
        ('muscle_count', 'Musculos distintos entrenados'),
        ('streak_days', 'Dias de racha'),
        ('exercise_count', 'Ejercicios en una sesion'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Facil'),
        ('medium', 'Media'),
        ('hard', 'Dificil'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    mission_type = models.CharField(max_length=10, choices=MISSION_TYPE_CHOICES)
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES)
    condition_value = models.PositiveIntegerField()
    condition_muscle = models.ForeignKey(
        'exercises.MuscleGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions'
    )
    xp_reward = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['mission_type', 'difficulty']

    def __str__(self):
        return f"[{self.mission_type}] {self.name} ({self.difficulty})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-58 — UserMission
# Representa la asignación de una misión
# a un usuario específico con su progreso
# status:
#   active    → en curso, aún puede completarse
#   completed → condicion cumplida, XP otorgada
#   expired   → venció sin completarse
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UserMission(models.Model):

    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('completed', 'Completada'),
        ('expired', 'Expirada'),
    ]

    # ← criterio  UUID PK
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ← criterio  FK al usuario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_missions'
    )

    # ← criterio FK a Mission
    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='user_missions'
    )

    # ← criterio fecha en que se asignó la misión
    assigned_date = models.DateField()

    # ← criterio progreso actual hacia el objetivo
    # se incrementa cada vez que el usuario completa
    # un workout y el MissionService evalúa
    current_progress = models.PositiveIntegerField(default=0)
    # ← criterio  copiado de mission.condition_value al asignar
    # snapshot del objetivo — no cambia aunque cambie la misión
    target_value = models.PositiveIntegerField()

    # ← criterio  estado de la misión del usuario
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    # ← criterio  null hasta que se complete
    completed_at = models.DateTimeField(null=True, blank=True)

    # ← criterio cuándo vence la misión
    # daily → assigned_date + 1 día
    # weekly → assigned_date + 7 días
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-assigned_date', 'status']

    def __str__(self):
        return f"{self.user.email} - {self.mission.name} ({self.status})"

    @property
    def progress_percentage(self):
        """Calcula el porcentaje de progreso hacia el objetivo."""
        if self.target_value == 0:
            return 100
        return min(100, int(self.current_progress / self.target_value * 100))