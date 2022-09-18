# Third Party
from rest_framework import permissions


class IsUsers(permissions.BasePermission):
    """Allows access only when user field matches user."""

    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False

        user_actions = [
            "create",
            "retrieve",
            "update",
            "destroy",
        ]

        return bool(view.action in user_actions or request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if not bool(request.user and request.user.is_authenticated):
            return False

        try:
            return obj.user == request.user
        except AttributeError:
            return False
