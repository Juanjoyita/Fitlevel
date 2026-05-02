# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/users/models.py
# Contiene: FT-18 (User) FT-19 (Profile) FT-20 (Signal)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-18 — UserManager
# Manager personalizado para crear usuarios
# con email como campo de login
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-18 — User
# Modelo de usuario personalizado
# USERNAME_FIELD = email (login con email)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-19 — Profile
# Perfil RPG del usuario
# OneToOne con User via related_name='profile'
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(       # campo para foto de perfil
        upload_to='avatars/',
        null=True,
        blank=True
    )
    total_xp = models.PositiveIntegerField(default=0)
    current_level = models.PositiveIntegerField(default=1)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_workout_date = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return f"Profile de {self.user.email}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-20 — Signal post_save
# Crea automáticamente un Profile
# cada vez que se crea un User nuevo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:  # solo en creación, no en updates
        Profile.objects.create(
            user=instance,
            display_name=instance.username  # nombre inicial = username
        )