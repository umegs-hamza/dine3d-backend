from rest_framework.permissions import BasePermission

from .models import User


class IsAdmin(BasePermission):
    """Allows access only to platform ADMIN users. `role` is checked explicitly —
    `is_staff` alone is never sufficient for platform (React admin dashboard) access."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN
        )


# Alias used by the /api/v1/admin/ namespace for a self-documenting import name.
IsAdminUserRole = IsAdmin


class IsRestaurantOwner(BasePermission):
    """Allows access only to RESTAURANT_OWNER users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.RESTAURANT_OWNER
        )


class IsAdminOrRestaurantOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
