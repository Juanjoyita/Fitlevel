# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/achievements/services.py
# FT-64 — AchievementService
# Verifica y desbloquea logros del usuario
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.utils import timezone
from .models import Achievement, UserAchievement


def _check_condition(user, achievement):
    """
    Verifica si el usuario cumple la condición del logro.
    Args:
        user: instancia del User
        achievement: instancia del Achievement a verificar
    Returns:
        True si la condición se cumple, False si no
    """
    profile = user.profile
    condition_type = achievement.condition_type
    condition_value = achievement.condition_value
    if condition_type == 'streak':
        # ← Racha de N días consecutivos
        return profile.current_streak >= condition_value
    elif condition_type == 'level':
        # ← Nivel general N alcanzado
        return profile.current_level >= condition_value
    elif condition_type == 'total_xp':
        # ← XP total acumulada
        return profile.total_xp >= condition_value
    elif condition_type == 'workout_count':
        # ← N sesiones completadas en total
        count = user.workouts.filter(is_completed=True).count()
        return count >= condition_value
    elif condition_type == 'mission_count':
        # ← N misiones completadas en total
        count = user.user_missions.filter(status='completed').count()
        return count >= condition_value
    elif condition_type == 'muscle_level':
        # ← Nivel N en un músculo específico
        # condition_muscle define cuál músculo
        if not achievement.condition_muscle:
            return False
        from apps.gamification.models import MuscleProgress
        try:
            progress = MuscleProgress.objects.get(
                user=user,
                muscle_group=achievement.condition_muscle
            )
            return progress.current_level >= condition_value
        except MuscleProgress.DoesNotExist:
            return False
    return False


def _grant_achievement_xp(user, achievement, workout=None):
    """
    Otorga XP de recompensa al usuario por desbloquear un logro.
    Actualiza profile.total_xp y current_level.
    Registra XPTransaction con source='achievement'.
    """
    profile = user.profile
    profile.total_xp += achievement.xp_reward

    from apps.gamification.services.level_service import calculate_level_from_xp
    new_level, _ = calculate_level_from_xp(profile.total_xp)
    profile.current_level = new_level
    profile.save(update_fields=['total_xp', 'current_level'])

    from apps.gamification.models import XPTransaction
    XPTransaction.objects.create(
        user=user,
        workout=workout,
        amount=achievement.xp_reward,
        source='achievement',           # ← criterio ✅
        description=f'+{achievement.xp_reward} XP por logro: {achievement.name}'
    )

def check_achievements(user, workout=None):
    """
    Verifica y desbloquea logros del usuario.
    Flujo:
    1. Obtiene IDs de logros ya desbloqueados → criterio ✅
    2. Filtra logros activos no desbloqueados → criterio ✅
    3. Verifica condición de cada logro → criterio ✅
    4. Si se cumple → get_or_create UserAchievement → criterio ✅
    5. Otorga XP reward → criterio ✅
    6. Registra XPTransaction → criterio ✅
    7. Devuelve lista de logros desbloqueados → criterio ✅
    """
    unlocked_ids = UserAchievement.objects.filter(
        user=user
    ).values_list('achievement_id', flat=True)
    # ← criterio ✅ logros activos aún no desbloqueados
    pending_achievements = Achievement.objects.filter(
        is_active=True
    ).exclude(
        id__in=unlocked_ids
    ).select_related('condition_muscle')
    newly_unlocked = []
    for achievement in pending_achievements:
        # ← criterio ✅ verifica condición
        if not _check_condition(user, achievement):
            continue
        # ← criterio ✅ get_or_create → idempotente
        # Si por alguna razón ya existe no duplica
        user_achievement, created = UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement,
            defaults={'unlocked_at': timezone.now()}
        )
        if created:
            _grant_achievement_xp(user, achievement, workout)
            newly_unlocked.append({
                'achievement_name': achievement.name,
                'description': achievement.description,
                'rarity': achievement.rarity,
                'badge_icon': achievement.badge_icon,
                'xp_reward': achievement.xp_reward,
            })
    return newly_unlocked