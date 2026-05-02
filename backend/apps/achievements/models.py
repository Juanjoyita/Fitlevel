# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/achievements/models.py
# Contiene: FT-62 (Achievement) FT-63 (UserAchievement)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
from django.conf import settings
from django.db import models


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-62 — Achievement
# Define un logro que el usuario puede
# desbloquear al cumplir una condición
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Achievement(models.Model):

    RARITY_CHOICES = [
        ('common', 'Común'),
        ('uncommon', 'Poco común'),
        ('rare', 'Raro'),
        ('epic', 'Épico'),
        ('legendary', 'Legendario'),
    ]

    CONDITION_TYPE_CHOICES = [
        ('streak', 'Racha de días consecutivos'),
        ('level', 'Nivel general alcanzado'),
        ('total_xp', 'XP total acumulada'),
        ('muscle_level', 'Nivel en músculo específico'),
        ('workout_count', 'Sesiones completadas'),
        ('mission_count', 'Misiones completadas'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES)
    condition_value = models.PositiveIntegerField()
    condition_muscle = models.ForeignKey(
        'exercises.MuscleGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='achievements'
    )
    xp_reward = models.PositiveIntegerField()
    rarity = models.CharField(max_length=10, choices=RARITY_CHOICES)
    badge_icon = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True) 

    class Meta:
        ordering = ['rarity', 'condition_value']

    def __str__(self):
        return f"[{self.rarity}] {self.name}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-63 — UserAchievement
# Registra el desbloqueo de un logro
# por un usuario específico
#
# unique_together → garantiza idempotencia
# Un logro no puede desbloquearse dos veces
# El servicio usa get_or_create para esto
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UserAchievement(models.Model):

    # ← criterio ✅ UUID PK
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # ← criterio ✅ FK al usuario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_achievements'
    )
    # ← criterio ✅ FK al Achievement
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements'
    )
    # ← criterio ✅ cuándo se desbloqueó
    # auto_now_add → se llena automáticamente al crear
    unlocked_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        # ← criterio ✅ garantiza que un logro
        # no se desbloquee más de una vez por usuario
        # el servicio usa get_or_create → idempotente
        unique_together = ('user', 'achievement')
        ordering = ['-unlocked_at']
    def __str__(self):
        return f"{self.user.email} desbloqueó {self.achievement.name}"