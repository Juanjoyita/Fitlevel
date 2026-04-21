# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/workouts/views.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Workout, WorkoutExercise, ExerciseSet
from .serializers import (
    WorkoutSerializer,
    WorkoutListSerializer,
    WorkoutExerciseSerializer,
    ExerciseSetSerializer,
)


class WorkoutListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkoutSerializer
        return WorkoutListSerializer

    def get_queryset(self):
        return Workout.objects.filter(
            user=self.request.user
        ).prefetch_related('workout_exercises')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        active_workout = Workout.objects.filter(
            user=request.user,
            is_completed=False
        ).first()

        if active_workout:
            return Response(
                {
                    'error': 'Ya tienes una sesión activa.',
                    'workout_id': str(active_workout.id),
                    'message': 'Completa o elimina la sesión activa antes de crear una nueva.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)


class WorkoutExerciseCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutExerciseSerializer

    def get_workout(self):
        try:
            return Workout.objects.get(
                id=self.kwargs['workout_id'],
                user=self.request.user
            )
        except Workout.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        workout = self.get_workout()

        if not workout:
            return Response(
                {'error': 'Sesión no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if workout.is_completed:
            return Response(
                {'error': 'No puedes agregar ejercicios a una sesión completada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            last_order = workout.workout_exercises.count()
            serializer.save(workout=workout, order=last_order + 1)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseSetCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSetSerializer

    def get_workout_exercise(self):
        try:
            return WorkoutExercise.objects.get(
                id=self.kwargs['exercise_id'],
                workout__id=self.kwargs['workout_id'],
                workout__user=self.request.user
            )
        except WorkoutExercise.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        workout_exercise = self.get_workout_exercise()

        if not workout_exercise:
            return Response(
                {'error': 'Ejercicio no encontrado en esta sesión.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if workout_exercise.workout.is_completed:
            return Response(
                {'error': 'No puedes agregar series a una sesión completada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            last_set = workout_exercise.sets.count()
            serializer.save(
                workout_exercise=workout_exercise,
                set_number=last_set + 1
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkoutCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workout_id):
        try:
            workout = Workout.objects.prefetch_related(
                'workout_exercises__exercise__exercise_muscles',
                'workout_exercises__sets'
            ).get(id=workout_id, user=request.user)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Sesión no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if workout.is_completed:
            return Response(
                {'error': 'Esta sesión ya fue completada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not workout.workout_exercises.exists():
            return Response(
                {'error': 'No puedes completar una sesión sin ejercicios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marca como completada antes de llamar al servicio
        workout.is_completed = True
        workout.finished_at = timezone.now()
        workout.save(update_fields=['is_completed', 'finished_at'])

        # ← FT-55 Llama al WorkoutCompletionService orquestador
        from apps.gamification.services import complete_workout
        result = complete_workout(workout)

        return Response(result, status=status.HTTP_200_OK)