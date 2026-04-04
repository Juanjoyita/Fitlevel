from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('auth/', include('apps.users.urls')),
        path('exercises/', include('apps.exercises.urls')),
        path('workouts/', include('apps.workouts.urls')),
        path('muscles/', include('apps.gamification.urls')),
        path('missions/', include('apps.missions.urls')),
        path('achievements/', include('apps.achievements.urls')),
    ])),
]