from rest_framework.permissions import BasePermission

from accounts.models import User


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission for Category/Product/Product3DModel: ADMIN can
    access anything; a RESTAURANT_OWNER only their own restaurant's data."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True

        restaurant = self._resolve_restaurant(obj)
        return restaurant is not None and restaurant.owner_id == request.user.id

    @staticmethod
    def _resolve_restaurant(obj):
        if hasattr(obj, "restaurant"):
            return obj.restaurant
        if hasattr(obj, "product"):
            return obj.product.restaurant
        return None
