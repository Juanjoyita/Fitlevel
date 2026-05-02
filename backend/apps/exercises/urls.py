# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/exercises/urls.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.urls import path
from .views import ExerciseListView, ExerciseDetailView

urlpatterns = [
    # FT-36 — Lista de ejercicios con filtros
    # GET /api/v1/exercises/
    # GET /api/v1/exercises/?muscle=chest
    # GET /api/v1/exercises/?category=cardio
    path('', ExerciseListView.as_view(), name='exercise-list'),

    # FT-36 — Detalle de ejercicio con músculos
    # GET /api/v1/exercises/{id}/
    path('<int:pk>/', ExerciseDetailView.as_view(), name='exercise-detail'),
]