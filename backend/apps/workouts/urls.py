
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/workouts/urls.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.urls import path
from .views import (
    WorkoutListCreateView,
    WorkoutExerciseCreateView,
    ExerciseSetCreateView,
    WorkoutCompleteView,
)

urlpatterns = [
    # FT-43 + FT-47 — Crear sesión y ver historial
    path('', WorkoutListCreateView.as_view(), name='workout-list-create'),
    # FT-44 — Agregar ejercicio a sesión
    path('<uuid:workout_id>/exercises/', WorkoutExerciseCreateView.as_view(), name='workout-exercise-create'),
    # FT-45 — Agregar serie a ejercicio
    path('<uuid:workout_id>/exercises/<uuid:exercise_id>/sets/', ExerciseSetCreateView.as_view(), name='exercise-set-create'),
    # FT-46 — Completar sesión
    path('<uuid:workout_id>/complete/', WorkoutCompleteView.as_view(), name='workout-complete'),
]