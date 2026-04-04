# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/exercises/models.py
# Contiene: FT-28 (MuscleGroup) FT-29 (Exercise)
#           FT-30 (ExerciseMuscle)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.db import models


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-28 — MuscleGroup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MuscleGroup(models.Model):

    BODY_ZONE_CHOICES = [
        ('front', 'Frente'),
        ('back', 'Espalda'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    body_zone = models.CharField(
        max_length=10,
        choices=BODY_ZONE_CHOICES
    )
    svg_element_id = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        db_table = 'muscle_groups'

    def __str__(self):
        return self.name


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-29 — Exercise
# category = 'strength' → trabaja músculos
#            → gana XP por músculo
# category = 'cardio'   → no trabaja músculo
#            → gana XP general al perfil
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Exercise(models.Model):

    DIFFICULTY_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
    ]

    CATEGORY_CHOICES = [
        ('strength', 'Fuerza'),   # trabaja grupos musculares específicos
        ('cardio', 'Cardio'),     # trabajo cardiovascular, XP general
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=15,
        choices=DIFFICULTY_CHOICES
    )
    # strength → XP por músculo via ExerciseMuscle
    # cardio   → XP directo al profile.total_xp
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='strength'        # la mayoría son de fuerza
    )
    base_xp = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Solo aplica a ejercicios de fuerza (category='strength')
    # Los ejercicios de cardio no tienen músculos asociados
    muscle_groups = models.ManyToManyField(
        MuscleGroup,
        through='ExerciseMuscle',
        related_name='exercises',
        blank=True                # blank=True → cardio no necesita músculos
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()} - {self.difficulty})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-30 — ExerciseMuscle
# Tabla intermedia entre Exercise y MuscleGroup
# Solo para ejercicios de fuerza
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ExerciseMuscle(models.Model):

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='exercise_muscles'
    )
    muscle_group = models.ForeignKey(
        MuscleGroup,
        on_delete=models.CASCADE,
        related_name='exercise_muscles'
    )
    is_primary = models.BooleanField(default=False)
    xp_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0
    )

    class Meta:
        unique_together = ('exercise', 'muscle_group')
        ordering = ['exercise', 'muscle_group']

    def __str__(self):
        primary = 'primario' if self.is_primary else 'secundario'
        return f"{self.exercise.name} → {self.muscle_group.name} ({primary})"