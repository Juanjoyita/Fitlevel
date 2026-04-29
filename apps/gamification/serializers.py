# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/gamification/serializers.py
# FT-67 — Serializers para el Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import serializers
from .models import MuscleProgress, XPTransaction
from apps.missions.models import UserMission
from apps.achievements.models import UserAchievement
from apps.workouts.models import Workout


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializer de perfil RPG para dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DashboardProfileSerializer(serializers.Serializer):
    display_name = serializers.CharField()
    total_xp = serializers.IntegerField()
    current_level = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    last_workout_date = serializers.DateField()
    timezone = serializers.CharField()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializer de misiones activas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ActiveMissionSerializer(serializers.ModelSerializer):
    mission_name = serializers.CharField(source='mission.name')
    mission_type = serializers.CharField(source='mission.mission_type')
    difficulty = serializers.CharField(source='mission.difficulty')
    xp_reward = serializers.IntegerField(source='mission.xp_reward')
    progress_percentage = serializers.IntegerField()

    class Meta:
        model = UserMission
        fields = [
            'id',
            'mission_name',
            'mission_type',
            'difficulty',
            'xp_reward',
            'current_progress',
            'target_value',
            'progress_percentage',
            'expires_at',
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializer de progreso muscular
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MuscleProgressSerializer(serializers.ModelSerializer):
    muscle_name = serializers.CharField(source='muscle_group.name')
    muscle_slug = serializers.CharField(source='muscle_group.slug')
    body_zone = serializers.CharField(source='muscle_group.body_zone')
    svg_element_id = serializers.CharField(source='muscle_group.svg_element_id')

    class Meta:
        model = MuscleProgress
        fields = [
            'muscle_name',
            'muscle_slug',
            'body_zone',
            'svg_element_id',
            'current_level',
            'current_xp',
            'total_xp_earned',
            'last_trained_at',
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializer de logros recientes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class RecentAchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='achievement.name')
    description = serializers.CharField(source='achievement.description')
    rarity = serializers.CharField(source='achievement.rarity')
    badge_icon = serializers.CharField(source='achievement.badge_icon')
    xp_reward = serializers.IntegerField(source='achievement.xp_reward')

    class Meta:
        model = UserAchievement
        fields = [
            'achievement_name',
            'description',
            'rarity',
            'badge_icon',
            'xp_reward',
            'unlocked_at',
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializer del último workout
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class LastWorkoutSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField()

    class Meta:
        model = Workout
        fields = [
            'id',
            'started_at',
            'finished_at',
            'total_xp_gained',
            'exercise_count',
        ]

    def get_exercise_count(self, obj):
        return obj.workout_exercises.count()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializer de transacciones XP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class XPTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XPTransaction
        fields = [
            'amount',
            'source',
            'description',
            'created_at',
        ]
