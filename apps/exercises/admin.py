# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/exercises/admin.py
# FT-37 — Admin con ExerciseMuscleInline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.contrib import admin
from .models import Exercise, MuscleGroup, ExerciseMuscle


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-37 — ExerciseMuscleInline
# TabularInline para editar ExerciseMuscle desde ExerciseAdmin
# Permite asignar músculos y xp_multiplier
# directamente desde la página del ejercicio
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseMuscleInline(admin.TabularInline):
    model = ExerciseMuscle
    extra = 1                    # muestra 1 fila vacía para agregar
    fields = [
        'muscle_group',          # asignar músculo
        'is_primary',            # músculo principal o secundario
        'xp_multiplier',         # criterio asignar multiplicador XP
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-37 — ExerciseAdmin
# Registra Exercise con ExerciseMuscleInline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    inlines = [ExerciseMuscleInline]  # TabularInline de ExerciseMuscle

    # Columnas visibles en la lista de ejercicios
    list_display = [
        'name',
        'category',
        'difficulty',
        'base_xp',
        'is_active',
    ]

    # Filtros en la barra lateral 
    list_filter = ['difficulty', 'is_active', 'category']

    # Búsqueda por nombre 
    search_fields = ['name']

    # Orden por defecto
    ordering = ['name']


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-37 — MuscleGroupAdmin
# Vista del catálogo de grupos musculares
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'body_zone', 'order']
    search_fields = ['name', 'slug']
    ordering = ['order']