# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/services/streak_service.py
# FT-54 — StreakService
# Actualiza la racha del usuario usando su timezone
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from datetime import timedelta
import pytz
from django.utils import timezone


def update_streak(user):
    """
    Actualiza la racha de entrenamiento del usuario.
    """
    profile = user.profile
    # Obtiene la timezone del usuario → criterio ✅
    try:
        user_tz = pytz.timezone(profile.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        user_tz = pytz.UTC

    # Fecha actual en la timezone del usuario → criterio ✅
    # podría perder su racha si entrena antes de medianoche UTC
    now_local = timezone.now().astimezone(user_tz)
    today = now_local.date()

    last_date = profile.last_workout_date

    if last_date is None:
        # ← criterio ✅ primer entrenamiento → streak = 1
        profile.current_streak = 1

    elif last_date == today:
        # ← criterio ✅ ya entrenó hoy → no cambia nada
        # evita incrementar si completa varios workouts en un día
        pass

    elif last_date == today - timedelta(days=1):
        # ← criterio ✅ entrenó ayer → racha continúa
        profile.current_streak += 1

    else:
        # ← criterio ✅ saltó días → racha se rompe y resetea a 1
        profile.current_streak = 1

    # Actualiza longest_streak si la racha actual lo supera
    # → criterio ✅
    if profile.current_streak > profile.longest_streak:
        profile.longest_streak = profile.current_streak

    # Actualiza la fecha del último entrenamiento
    profile.last_workout_date = today

    # update_fields → eficiencia → criterio ✅
    # solo actualiza los campos que cambiaron
    # evita sobreescribir otros campos del profile
    profile.save(update_fields=[
        'current_streak',
        'longest_streak',
        'last_workout_date',
    ])

    return profile