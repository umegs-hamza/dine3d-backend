from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from config.responses import success_response

from .models import Restaurant
from .permissions import IsOwnerOrAdmin
from .serializers import RestaurantSerializer


class RestaurantViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List-only endpoint for restaurants. Admins see all restaurants; owners see
    only their own. Create/retrieve/update/destroy are not exposed via the API."""

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
