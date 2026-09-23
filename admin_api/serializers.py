from rest_framework import serializers

from accounts.models import User
from menu.models import Category, Product, Product3DModel
from restaurants.models import Restaurant


class AdminUserSerializer(serializers.ModelSerializer):
    """Read/activate-only — the React admin dashboard must never change passwords."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "first_name", "last_name", "role", "created_at", "updated_at"]


class AdminRestaurantSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "owner",
            "owner_email",
            "owner_name",
            "name",
            "slug",
            "description",
            "logo",
            "cover_image",
            "address",
            "city",
            "phone",
            "is_published",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "owner_email", "owner_name", "slug", "created_at", "updated_at"]


class AdminCategorySerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "name",
            "description",
            "image",
            "sort_order",
            "is_active",
            "products_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AdminProductSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    has_3d_model = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "image",
            "is_available",
            "is_featured",
            "sort_order",
            "has_3d_model",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_has_3d_model(self, product):
        return hasattr(product, "model_3d") and product.model_3d is not None


class AdminProduct3DModelSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    restaurant_name = serializers.CharField(source="product.restaurant.name", read_only=True)
    restaurant_id = serializers.IntegerField(source="product.restaurant_id", read_only=True)

    class Meta:
        model = Product3DModel
        fields = [
            "id",
            "product",
            "product_name",
            "restaurant_id",
            "restaurant_name",
            "model_file",
            "model_url",
            "format",
            "is_ar_enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_restaurants = serializers.IntegerField()
    published_restaurants = serializers.IntegerField()
    unpublished_restaurants = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_products = serializers.IntegerField()
    available_products = serializers.IntegerField()
    total_3d_models = serializers.IntegerField()
