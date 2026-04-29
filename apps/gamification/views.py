# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/views.py
# FT-67 — DashboardView
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.missions.services import assign_daily_missions, assign_weekly_missions
from apps.gamification.models import MuscleProgress, XPTransaction
from apps.missions.models import UserMission
from apps.achievements.models import UserAchievement
from apps.workouts.models import Workout
from .serializers import (
    DashboardProfileSerializer,
    ActiveMissionSerializer,
    MuscleProgressSerializer,
    RecentAchievementSerializer,
    LastWorkoutSerializer,
    XPTransactionSerializer,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-67 — DashboardView
# GET /api/v1/dashboard/
# Agrega todos los datos del usuario en
# una sola llamada para Flutter
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ← criterio ✅ asigna misiones si no tiene para hoy
        assign_daily_missions(user)
        assign_weekly_missions(user)

        # ← criterio ✅ perfil del usuario
        profile = user.profile

        # ← criterio ✅ misiones activas máximo 5
        active_missions = UserMission.objects.filter(
            user=user,
            status='active'
        ).select_related('mission')[:5]

        # ← criterio ✅ MuscleProgress ordenado por last_trained_at
        muscle_progress = MuscleProgress.objects.filter(
            user=user
        ).select_related(
            'muscle_group'
        ).order_by('-last_trained_at')

        # ← criterio ✅ últimos 3 UserAchievements
        recent_achievements = UserAchievement.objects.filter(
            user=user
        ).select_related('achievement')[:3]

        # ← criterio ✅ último Workout completado
        last_workout = Workout.objects.filter(
            user=user,
            is_completed=True
        ).prefetch_related('workout_exercises').first()

        # ← criterio ✅ últimas 10 XPTransactions
        xp_transactions = XPTransaction.objects.filter(
            user=user
        )[:10]

        # Serializa y retorna todo en un único JSON → criterio ✅
        return Response({
            'profile': DashboardProfileSerializer(profile).data,
            'active_missions': ActiveMissionSerializer(
                active_missions, many=True
            ).data,
            'muscle_progress': MuscleProgressSerializer(
                muscle_progress, many=True
            ).data,
            'recent_achievements': RecentAchievementSerializer(
                recent_achievements, many=True
            ).data,
            'last_workout': LastWorkoutSerializer(last_workout).data
                if last_workout else None,
            'xp_transactions': XPTransactionSerializer(
                xp_transactions, many=True
            ).data,
        }, status=status.HTTP_200_OK)
