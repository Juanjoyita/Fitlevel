# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/services/__init__.py
# FT-55 — WorkoutCompletionService
# Orquestador atómico del flujo de gamificación
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.db import transaction
from django.utils import timezone

from apps.gamification.models import MuscleProgress, XPTransaction
from apps.gamification.services.xp_service import calculate_workout_xp
from apps.gamification.services.level_service import calculate_level_from_xp
from apps.gamification.services.streak_service import update_streak


def _update_muscle_progress(user, muscle_xp_dict, workout):
    """
    Actualiza o crea el progreso muscular para cada músculo
    que recibió XP en este workout.

    Usa get_or_create → idempotente, no duplica registros.
    Registra cada ganancia en XPTransaction (inmutable).

    Args:
        user: usuario autenticado
        muscle_xp_dict: {muscle_group_id: xp_ganada}
        workout: instancia del Workout completado

    Returns:
        lista de dicts con el progreso actualizado por músculo
    """
    muscle_results = []

    for muscle_group_id, xp_gained in muscle_xp_dict.items():
        if xp_gained <= 0:
            continue

        # get_or_create → crea el registro si no existe
        # evita duplicados por unique_together (user, muscle_group)
        muscle_progress, created = MuscleProgress.objects.get_or_create(
            user=user,
            muscle_group_id=muscle_group_id,
            defaults={
                'current_xp': 0,
                'current_level': 1,
                'total_xp_earned': 0,
            }
        )

        # Nivel anterior para detectar subida de nivel
        old_level = muscle_progress.current_level

        # Acumula XP en el total histórico → NUNCA se resetea
        muscle_progress.total_xp_earned += xp_gained

        # Recalcula nivel y XP actual desde el total histórico
        new_level, new_current_xp = calculate_level_from_xp(
            muscle_progress.total_xp_earned
        )

        muscle_progress.current_level = new_level
        muscle_progress.current_xp = new_current_xp
        muscle_progress.last_trained_at = timezone.now()
        muscle_progress.save()

        # Registra la transacción XP → inmutable → solo INSERT
        from apps.exercises.models import MuscleGroup
        muscle_group = MuscleGroup.objects.get(id=muscle_group_id)

        XPTransaction.objects.create(
            user=user,
            workout=workout,
            muscle_group_id=muscle_group_id,
            amount=xp_gained,
            source='workout',
            description=f'+{xp_gained} XP en {muscle_group.name}'
        )

        muscle_results.append({
            'muscle_group_id': muscle_group_id,
            'muscle_name': muscle_group.name,
            'xp_gained': xp_gained,
            'old_level': old_level,
            'new_level': new_level,
            'current_xp': new_current_xp,
            'leveled_up': new_level > old_level,
        })

    return muscle_results


def complete_workout(workout):
    """
    Orquestador principal del flujo de gamificación.
    Ejecuta todo dentro de una transacción atómica.

    Si cualquier paso falla → rollback completo
    No quedan estados inconsistentes en la BD.

    Flujo:
    1. calculate_workout_xp() → XP por músculo
    2. _update_muscle_progress() → actualiza MuscleProgress
    3. Actualiza profile.total_xp y current_level
    4. Guarda workout.total_xp_gained
    5. update_streak() → actualiza racha
    6. evaluate_missions() → evalúa misiones (Sprint 6)
    7. check_achievements() → verifica logros (Sprint 6)

    Args:
        workout: instancia de Workout ya marcada como completada

    Returns:
        dict con todos los resultados de la gamificación
    """
    with transaction.atomic():
        user = workout.user
        profile = user.profile

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 1 — Calcular XP por músculo
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        muscle_xp_dict = calculate_workout_xp(workout)

        # XP total de este workout = suma de todos los músculos
        total_xp_this_workout = sum(muscle_xp_dict.values())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 2 — Actualizar progreso muscular
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        muscle_results = _update_muscle_progress(
            user=user,
            muscle_xp_dict=muscle_xp_dict,
            workout=workout
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 3 — Actualizar perfil general
        # Nivel general = calculate_level_from_xp(profile.total_xp)
        # NUNCA el promedio de niveles musculares
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        old_profile_level = profile.current_level
        profile.total_xp += total_xp_this_workout

        new_profile_level, _ = calculate_level_from_xp(profile.total_xp)
        profile.current_level = new_profile_level

        profile.save(update_fields=['total_xp', 'current_level'])

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 4 — Guardar XP total en el workout
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workout.total_xp_gained = total_xp_this_workout
        workout.save(update_fields=['total_xp_gained'])

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 5 — Actualizar racha
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        updated_profile = update_streak(user)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 6 — Evaluar misiones (Sprint 6)
        # Placeholder hasta implementar MissionService
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        completed_missions = []
        try:
            from apps.missions.services import evaluate_missions
            completed_missions = evaluate_missions(user, workout)
        except (ImportError, Exception):
            pass

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 7 — Verificar logros (Sprint 6)
        # Placeholder hasta implementar AchievementService
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        unlocked_achievements = []
        try:
            from apps.achievements.services import check_achievements
            unlocked_achievements = check_achievements(user)
        except (ImportError, Exception):
            pass

        # Devuelve resumen completo para Flutter
        return {
            'total_xp_gained': total_xp_this_workout,
            'muscle_results': muscle_results,
            'profile': {
                'total_xp': profile.total_xp,
                'current_level': new_profile_level,
                'leveled_up': new_profile_level > old_profile_level,
                'current_streak': updated_profile.current_streak,
                'longest_streak': updated_profile.longest_streak,
            },
            'completed_missions': completed_missions,
            'unlocked_achievements': unlocked_achievements,
        }