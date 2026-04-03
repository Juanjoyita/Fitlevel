# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHIVO: apps/users/admin.py
# FT-26 — Admin de users con ProfileInline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-26 — ProfileInline
# Se incrusta dentro de UserAdmin
# Muestra el perfil RPG dentro de la
# página del User en el admin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Perfil RPG'
    verbose_name_plural = 'Perfil RPG'
    # estos 4 campos no se pueden editar manualmente
    # son gestionados exclusivamente por el sistema de gamificación
    readonly_fields = [
        'total_xp',        
        'current_level',   
        'current_streak',  
        'longest_streak',  
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-26 — UserAdmin
# extiende BaseUserAdmin
# incluye ProfileInline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]  # ProfileInline dentro de UserAdmin

    list_display = [
        'email',
        'username',
        'is_active',
        'is_staff',
        'date_joined',
    ]
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas', {
            'fields': ('date_joined', 'last_login')
        }),
    )
    readonly_fields = ['date_joined', 'last_login']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FT-26 — ProfileAdmin
# registrado por separado
# list_display muestra usuario, nivel y XP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',           # ←  usuario
        'current_level',  # ←  nivel
        'total_xp',       # ←  XP
    ]
    search_fields = ['user__email', 'display_name']
    readonly_fields = [
        'total_xp',
        'current_level',
        'current_streak',
        'longest_streak',
    ]