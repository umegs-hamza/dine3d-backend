from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User
from config.responses import error_response, success_response
from restaurants.models import Restaurant

from .models import Category, Product, Product3DModel
from .permissions import IsOwnerOrAdmin
from .serializers import (
    CategorySerializer,
    CategoryWithProductsPublicSerializer,
    Product3DModelSerializer,
    ProductSerializer,
)


class _StandardResponseModelViewSet(viewsets.ModelViewSet):
    """Shared CRUD behavior returning the platform's standard response envelope."""

    entity_name = "Resource"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        data = serializer.data
        if page is not None:
            return self.get_paginated_response(data)
        return success_response(data=data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return success_response(
            data=self.get_serializer(instance).data,
            message=f"{self.entity_name} created successfully.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return success_response(
            data=self.get_serializer(updated).data, message=f"{self.entity_name} updated successfully."
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message=f"{self.entity_name} deleted successfully.")


class CategoryViewSet(_StandardResponseModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["restaurant", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["sort_order", "name", "created_at"]
    entity_name = "Category"

    def get_queryset(self):
        user = self.request.user
        qs = Category.objects.select_related("restaurant")
        if user.role == User.Role.ADMIN:
            return qs
        return qs.filter(restaurant__owner=user)


class ProductViewSet(_StandardResponseModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["restaurant", "category", "is_available", "is_featured"]
    search_fields = ["name", "description"]
    ordering_fields = ["sort_order", "name", "price", "created_at"]
    entity_name = "Product"

    def get_queryset(self):
        user = self.request.user
        qs = Product.objects.select_related("restaurant", "category")
        if user.role == User.Role.ADMIN:
            return qs
        return qs.filter(restaurant__owner=user)


class Product3DModelView(APIView):
    """GET/POST/PATCH/DELETE the (optional) 3D model attached to a single product,
    nested under /products/{product_id}/3d/."""

    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def _get_product(self, request, product_id):
        user = request.user
        qs = Product.objects.select_related("restaurant")
        if user.role != User.Role.ADMIN:
            qs = qs.filter(restaurant__owner=user)
        return get_object_or_404(qs, pk=product_id)

    def get(self, request, product_id):
        product = self._get_product(request, product_id)
        model = getattr(product, "model_3d", None)
        if not model:
            return error_response(message="This product has no 3D model.", status=status.HTTP_404_NOT_FOUND)
        return success_response(data=Product3DModelSerializer(model).data)

    def post(self, request, product_id):
        product = self._get_product(request, product_id)
        if hasattr(product, "model_3d"):
            return error_response(
                message="This product already has a 3D model. Use PATCH to update it.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = Product3DModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        model = serializer.save(product=product)
        return success_response(
            data=Product3DModelSerializer(model).data,
            message="3D model uploaded successfully.",
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, product_id):
        product = self._get_product(request, product_id)
        model = getattr(product, "model_3d", None)
        if not model:
            return error_response(message="This product has no 3D model.", status=status.HTTP_404_NOT_FOUND)
        serializer = Product3DModelSerializer(model, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return success_response(data=Product3DModelSerializer(updated).data, message="3D model updated successfully.")

    def delete(self, request, product_id):
        product = self._get_product(request, product_id)
        model = getattr(product, "model_3d", None)
        if not model:
            return error_response(message="This product has no 3D model.", status=status.HTTP_404_NOT_FOUND)
        model.delete()
        return success_response(message="3D model deleted successfully.")


class PublicRestaurantListView(APIView):
    """Public, unauthenticated listing of every published + active restaurant.
    Returns light restaurant cards only (no menus) — the menu is fetched per
    restaurant via PublicRestaurantMenuView."""

    permission_classes = [AllowAny]

    def get(self, request):
        from restaurants.serializers import RestaurantPublicSerializer

        restaurants = Restaurant.objects.filter(is_published=True, is_active=True).order_by("name")
        return success_response(data=RestaurantPublicSerializer(restaurants, many=True).data)


class PublicRestaurantMenuView(APIView):
    """Public, unauthenticated endpoint returning a published restaurant's full
    menu: only active categories and available products are included."""

    permission_classes = [AllowAny]

    def get(self, request, slug):
        restaurant = get_object_or_404(
            Restaurant.objects.filter(is_published=True, is_active=True), slug=slug
        )
        categories = (
            Category.objects.filter(restaurant=restaurant, is_active=True)
            .prefetch_related("products__model_3d")
            .order_by("sort_order", "name")
        )

        from restaurants.serializers import RestaurantPublicSerializer

        data = {
            "restaurant": RestaurantPublicSerializer(restaurant).data,
            "categories": CategoryWithProductsPublicSerializer(categories, many=True).data,
        }
        return success_response(data=data)
