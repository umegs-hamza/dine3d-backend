from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from config.responses import success_response

from .models import Restaurant
from .permissions import IsOwnerOrAdmin
from .serializers import RestaurantSerializer


class RestaurantViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD endpoint for restaurants scoped to the authenticated user."""

    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = RestaurantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "is_published", "is_active"]
    search_fields = ["name", "city", "address"]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        user = self.request.user
        qs = Restaurant.objects.select_related("owner")
        if user.role == User.Role.ADMIN:
            return qs
        return qs.filter(owner=user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        data = serializer.data
        if page is not None:
            return self.get_paginated_response(data)
        return success_response(data=data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        restaurant = serializer.save(owner=request.user)
        return success_response(
            data=self.get_serializer(restaurant).data,
            message="Restaurant created successfully.",
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        restaurant = self.get_object()
        return success_response(data=self.get_serializer(restaurant).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        restaurant = self.get_object()
        serializer = self.get_serializer(restaurant, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return success_response(
            data=self.get_serializer(updated).data,
            message="Restaurant updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        restaurant = self.get_object()
        restaurant.delete()
        return success_response(message="Restaurant deleted successfully.")
