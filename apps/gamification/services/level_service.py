# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/services/level_service.py
# FT-53 — LevelService
# Calcula niveles usando curva cuadrática 100 × n²
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def xp_required_for_level(n):
    """
    Calcula el XP necesario para subir AL nivel n.
    Fórmula: 100 × n²
    Args:
        n: nivel actual (el XP necesario para pasar del nivel n al n+1)

    Returns:
        XP necesaria para subir del nivel n al n+1
    """
    return 100 * (n ** 2)


def calculate_level_from_xp(total_xp):
    """
    Calcula el nivel actual y XP restante a partir del XP total acumulado.
    Itera restando XP nivel por nivel hasta que no quede suficiente
    para subir al siguiente nivel.
    Args:
        total_xp: XP total histórica acumulada (nunca se resetea)
    """
    level = 1
    remaining_xp = total_xp

    # Itera restando XP de nivel en nivel → criterio ✅
    # mientras tenga suficiente XP para subir al siguiente nivel
    while remaining_xp >= xp_required_for_level(level):
        remaining_xp -= xp_required_for_level(level)
        level += 1

    return level, remaining_xp