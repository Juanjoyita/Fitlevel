from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Permite acceso solo al dueño del objeto (obj.user == request.user)."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
