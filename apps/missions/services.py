# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/missions/services.py
# FT-59 — MissionService
# Asigna y evalúa misiones diarias y semanales
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import random
import pytz
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import Mission, UserMission


def _get_user_today(user):
    """
    Obtiene la fecha actual en la timezone del usuario.
    Crítico para asignar misiones diarias correctamente.
    """
    try:
        user_tz = pytz.timezone(user.profile.timezone)
    except Exception:
        user_tz = pytz.UTC
    return timezone.now().astimezone(user_tz).date()


def _get_midnight_local(user, date):
    """
    Devuelve las 23:59:59 de una fecha dada
    en la timezone del usuario como datetime UTC.
    """
    try:
        user_tz = pytz.timezone(user.profile.timezone)
    except Exception:
        user_tz = pytz.UTC
    naive_midnight = timezone.datetime(
        date.year, date.month, date.day, 23, 59, 59
    )
    local_midnight = user_tz.localize(naive_midnight)
    return local_midnight.astimezone(pytz.UTC)


def assign_daily_missions(user):
    """
    Asigna 3 misiones diarias al usuario si aún no tiene para hoy.
    Expiran a las 23:59 del mismo día en la timezone del usuario.
    """
    today = _get_user_today(user)

    # Verifica si ya tiene misiones activas para hoy
    already_assigned = UserMission.objects.filter(
        user=user,
        mission__mission_type='daily',
        assigned_date=today,
        status='active'
    ).exists()

    if already_assigned:
        return []

    # Obtiene todas las misiones diarias activas
    daily_missions = list(
        Mission.objects.filter(
            mission_type='daily',
            is_active=True
        )
    )

    if not daily_missions:
        return []

    # Selecciona 3 al azar → criterio ✅
    # Si hay menos de 3 misiones, toma todas
    count = min(3, len(daily_missions))
    selected = random.sample(daily_missions, count)

    # Calcula expiración → 23:59 de hoy
    expires_at = _get_midnight_local(user, today)

    created = []
    with transaction.atomic():
        for mission in selected:
            user_mission = UserMission.objects.create(
                user=user,
                mission=mission,
                assigned_date=today,
                current_progress=0,
                # ← copia snapshot de condition_value al asignar
                target_value=mission.condition_value,
                status='active',
                expires_at=expires_at
            )
            created.append(user_mission)

    return created


def assign_weekly_missions(user):
    """
    Asigna 2 misiones semanales el lunes.
    Expiran el domingo a las 23:59 en la timezone del usuario.

    ← criterio ✅ asigna el lunes
    ← criterio ✅ expiran el domingo a las 23:59
    """
    today = _get_user_today(user)

    # Solo asigna los lunes (weekday() == 0)
    if today.weekday() != 0:
        return []

    # Verifica si ya tiene misiones semanales esta semana
    already_assigned = UserMission.objects.filter(
        user=user,
        mission__mission_type='weekly',
        assigned_date=today,
        status='active'
    ).exists()

    if already_assigned:
        return []

    weekly_missions = list(
        Mission.objects.filter(
            mission_type='weekly',
            is_active=True
        )
    )

    if not weekly_missions:
        return []

    count = min(2, len(weekly_missions))
    selected = random.sample(weekly_missions, count)

    # Expira el domingo → today + (6 - weekday()) días
    # Si hoy es lunes (0) → sunday = today + 6
    sunday = today + timedelta(days=6)
    expires_at = _get_midnight_local(user, sunday)

    created = []
    with transaction.atomic():
        for mission in selected:
            user_mission = UserMission.objects.create(
                user=user,
                mission=mission,
                assigned_date=today,
                current_progress=0,
                target_value=mission.condition_value,
                status='active',
                expires_at=expires_at
            )
            created.append(user_mission)

    return created


def evaluate_missions(user, workout, xp_gained=0):
    """
    Evalúa y actualiza el progreso de las misiones activas del usuario.
    Se llama después de completar un workout."""

    today = _get_user_today(user)
    now = timezone.now()

    # Obtiene solo misiones activas no expiradas
    active_missions = UserMission.objects.filter(
        user=user,
        status='active',
        expires_at__gt=now
    ).select_related('mission', 'mission__condition_muscle')

    completed_missions = []

    with transaction.atomic():
        for user_mission in active_missions:
            mission = user_mission.mission
            new_progress = user_mission.current_progress

            # Calcula el progreso según el tipo de condición
            if mission.condition_type == 'workout_count':
                # Número de sesiones completadas hoy
                workout_count = workout.user.workouts.filter(
                    is_completed=True,
                    finished_at__date=today
                ).count()
                new_progress = workout_count

            elif mission.condition_type == 'xp_gained':
                # XP ganada en este workout
                new_progress = user_mission.current_progress + xp_gained

            elif mission.condition_type == 'exercise_count':
                # Ejercicios en esta sesión
                new_progress = workout.workout_exercises.count()

            elif mission.condition_type == 'muscle_count':
                # Músculos distintos entrenados en esta sesión
                from apps.exercises.models import ExerciseMuscle
                muscle_ids = ExerciseMuscle.objects.filter(
                    exercise__workout_exercises__workout=workout,
                    is_primary=True
                ).values_list('muscle_group_id', flat=True).distinct()
                new_progress = len(set(muscle_ids))

            elif mission.condition_type == 'streak_days':
                # Racha actual del usuario
                new_progress = user.profile.current_streak

            # Actualiza el progreso
            user_mission.current_progress = new_progress

            # Verifica si se completó → criterio ✅
            if new_progress >= user_mission.target_value:
                user_mission.status = 'completed'
                user_mission.completed_at = now

                # Otorga XP de recompensa al perfil
                profile = user.profile
                profile.total_xp += mission.xp_reward
                from apps.gamification.services.level_service import calculate_level_from_xp
                new_level, _ = calculate_level_from_xp(profile.total_xp)
                profile.current_level = new_level
                profile.save(update_fields=['total_xp', 'current_level'])

                # Registra la transacción XP de la misión
                from apps.gamification.models import XPTransaction
                XPTransaction.objects.create(
                    user=user,
                    workout=workout,
                    amount=mission.xp_reward,
                    source='mission',
                    description=f'+{mission.xp_reward} XP por mision: {mission.name}'
                )

                completed_missions.append({
                    'mission_name': mission.name,
                    'xp_reward': mission.xp_reward,
                    'difficulty': mission.difficulty,
                })

            user_mission.save(update_fields=['current_progress', 'status', 'completed_at'])

    return completed_missions


def expire_old_missions():
    """
    Marca como expiradas las misiones activas cuyo tiempo venció.
    Se debe llamar periódicamente (cron job o Celery beat).
    """
    now = timezone.now()
    expired_count = UserMission.objects.filter(
        status='active',
        expires_at__lte=now
    ).update(status='expired')
    return expired_count