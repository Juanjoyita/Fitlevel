# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/services/xp_service.py
# FT-52 — XPService
# Calcula XP por músculo para un workout completo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from decimal import Decimal

# Cap máximo de XP por músculo por sesión
# Evita abuso registrando demasiadas series
XP_CAP_PER_MUSCLE = 500


def calculate_volume_bonus(weight_kg):
    """
    Calcula el bonus de volumen basado en el peso usado.

    Fórmula: volume_bonus = min(1 + (weight_kg / 100) × 0.1, 1.5)

    Ejemplos:
    - peso corporal (None) → 1.0 (sin bonus)
    - 50kg  → min(1 + 0.05, 1.5) = 1.05
    - 100kg → min(1 + 0.10, 1.5) = 1.10
    - 500kg → min(1 + 0.50, 1.5) = 1.50 (máximo)
    """
    if weight_kg is None:
        # Ejercicio de peso corporal → sin bonus de volumen
        return Decimal('1.0')

    bonus = Decimal('1.0') + (Decimal(str(weight_kg)) / Decimal('100')) * Decimal('0.1')
    # Cap máximo de 1.5 → evita abuso con pesos irreales
    return min(bonus, Decimal('1.5'))


def calculate_set_xp(base_xp, xp_multiplier, weight_kg):
    """
    Calcula el XP de una sola serie.

    Fórmula: xp = base_xp × xp_multiplier × volume_bonus

    Args:
        base_xp: XP base del ejercicio (10/20/30 según dificultad)
        xp_multiplier: multiplicador del músculo (1.0 primario, 0.2-0.5 secundario)
        weight_kg: peso usado en la serie (None para peso corporal)

    Returns:
        XP calculada como entero redondeado
    """
    volume_bonus = calculate_volume_bonus(weight_kg)
    xp = Decimal(str(base_xp)) * Decimal(str(xp_multiplier)) * volume_bonus
    return int(xp)


def calculate_workout_xp(workout):
    """
    Calcula el XP total por músculo para un workout completo.

    Itera sobre todos los ejercicios y sus series completadas.
    Aplica la fórmula por cada músculo involucrado.
    Aplica cap de 500 XP por músculo por sesión.

    Returns:
        dict con muscle_group_id como clave y XP ganada como valor
        Ejemplo: {1: 150, 2: 45, 8: 80}
        donde 1=Pecho, 2=Hombros, 8=Tríceps
    """
    # Acumulador de XP por muscle_group_id
    muscle_xp = {}

    # Itera sobre cada ejercicio del workout
    for workout_exercise in workout.workout_exercises.all():
        exercise = workout_exercise.exercise

        # Los ejercicios de cardio no tienen músculos
        # → no acumulan XP por músculo
        if exercise.category == 'cardio':
            continue

        # Obtiene todos los músculos del ejercicio
        # con sus multiplicadores
        exercise_muscles = exercise.exercise_muscles.all()

        # Itera sobre cada serie completada
        # Solo completed=True cuenta para XP → criterio FT-41
        completed_sets = workout_exercise.sets.filter(completed=True)

        for exercise_set in completed_sets:
            # Calcula XP para cada músculo involucrado
            for exercise_muscle in exercise_muscles:
                muscle_id = exercise_muscle.muscle_group_id

                # Inicializa el acumulador si es la primera vez
                if muscle_id not in muscle_xp:
                    muscle_xp[muscle_id] = 0

                # Calcula XP de esta serie para este músculo
                set_xp = calculate_set_xp(
                    base_xp=exercise.base_xp,
                    xp_multiplier=exercise_muscle.xp_multiplier,
                    weight_kg=exercise_set.weight_kg
                )

                muscle_xp[muscle_id] += set_xp

    # Aplica cap de 500 XP por músculo → criterio ✅
    # Evita abuso registrando cientos de series
    for muscle_id in muscle_xp:
        muscle_xp[muscle_id] = min(muscle_xp[muscle_id], XP_CAP_PER_MUSCLE)

    return muscle_xp