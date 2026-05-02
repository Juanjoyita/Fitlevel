# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/models.py
# Contiene: FT-49 (MuscleProgress)
#           FT-50 (XPTransaction)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
from django.conf import settings
from django.db import models


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-49 — MuscleProgress
# Registra el progreso XP y nivel
# del usuario por cada grupo muscular
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MuscleProgress(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='muscle_progress'
    )
    muscle_group = models.ForeignKey(
        'exercises.MuscleGroup',
        on_delete=models.CASCADE,
        related_name='muscle_progress'
    )
    # XP dentro del nivel actual → se resetea al subir nivel
    current_xp = models.PositiveIntegerField(default=0)
    # Nivel actual → calculado desde total_xp_earned
    current_level = models.PositiveIntegerField(default=1)
    # XP histórica total → NUNCA se resetea → fuente de verdad
    total_xp_earned = models.PositiveIntegerField(default=0)
    last_trained_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'muscle_group')

    def __str__(self):
        return f"{self.user.email} - {self.muscle_group.name} Lv{self.current_level}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-50 — XPTransaction
# Log INMUTABLE de cada ganancia de XP
# Regla: NUNCA UPDATE ni DELETE
# Solo INSERT → append-only log
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class XPTransaction(models.Model):

    SOURCE_CHOICES = [
        ('workout', 'Entrenamiento'),
        ('mission', 'Misión'),
        ('achievement', 'Logro'),
        ('bonus', 'Bono'),
    ]

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
        related_name='xp_transactions'
    )

    # ← criterio ✅ null=True para misiones y logros
    # que no están asociados a un workout específico
    workout = models.ForeignKey(
        'workouts.Workout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='xp_transactions'
    )

    # ← criterio ✅ null=True para XP general
    # (racha, logros, misiones sin músculo específico)
    muscle_group = models.ForeignKey(
        'exercises.MuscleGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='xp_transactions'
    )

    # ← criterio ✅ cantidad de XP ganada
    amount = models.PositiveIntegerField()

    # ← criterio ✅ origen de la transacción
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES
    )

    # ← criterio ✅ texto legible para el usuario
    # ejemplo: '+63 XP en Pecho', '+50 XP por misión'
    description = models.CharField(max_length=255)

    # ← criterio ✅ auto_now_add → inmutable por diseño
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # Inmutabilidad garantizada por convención:
        # el servicio NUNCA llama .save() en registros existentes
        # ni .delete() — solo XPTransaction.objects.create()

    def save(self, *args, **kwargs):
        # ← criterio ✅ garantiza inmutabilidad a nivel de modelo
        # Si el registro ya existe (tiene pk guardado en BD)
        # lanza error — solo permite INSERT nunca UPDATE
        if self._state.adding is False:
            raise ValueError(
                'XPTransaction es inmutable. No se puede editar un registro existente.'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # ← criterio ✅ bloquea eliminación a nivel de modelo
        raise ValueError(
            'XPTransaction es inmutable. No se puede eliminar un registro.'
        )

    def __str__(self):
        return f"{self.user.email} +{self.amount} XP ({self.source}) - {self.description}"