from rest_framework import serializers

from accounts.models import User
from restaurants.models import Restaurant

from .models import Category, Product, Product3DModel


class Product3DModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product3DModel
        fields = [
            "id",
            "product",
            "model_file",
            "model_url",
            "format",
            "is_ar_enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "product", "created_at", "updated_at"]

    def validate(self, attrs):
        model_file = attrs.get("model_file", getattr(self.instance, "model_file", None))
        model_url = attrs.get("model_url", getattr(self.instance, "model_url", ""))
        if not model_file and not model_url:
            raise serializers.ValidationError("Either model_file or model_url must be provided.")
        return attrs


class Product3DModelPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product3DModel
        fields = ["model_url", "format", "is_ar_enabled"]
        read_only_fields = fields


def _owned_restaurants_queryset(request):
    if request.user.role == User.Role.ADMIN:
        return Restaurant.objects.all()
    return Restaurant.objects.filter(owner=request.user)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "restaurant",
            "name",
            "description",
            "image",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_restaurant(self, restaurant):
        request = self.context["request"]
        if not _owned_restaurants_queryset(request).filter(pk=restaurant.pk).exists():
            raise serializers.ValidationError("You do not own this restaurant.")
        return restaurant


class CategoryPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "image"]
        read_only_fields = fields


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "restaurant",
            "category",
            "name",
            "description",
            "price",
            "image",
            "is_available",
            "is_featured",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        restaurant = attrs.get("restaurant", getattr(self.instance, "restaurant", None))
        category = attrs.get("category", getattr(self.instance, "category", None))

        if restaurant and not _owned_restaurants_queryset(request).filter(pk=restaurant.pk).exists():
            raise serializers.ValidationError({"restaurant": "You do not own this restaurant."})

        if category and restaurant and category.restaurant_id != restaurant.id:
            raise serializers.ValidationError(
                {"category": "Category must belong to the same restaurant as the product."}
            )
        return attrs


class ProductPublicSerializer(serializers.ModelSerializer):
    model_3d = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "image", "is_available", "model_3d"]
        read_only_fields = fields

    def get_model_3d(self, product):
        model = getattr(product, "model_3d", None)
        if not model:
            return None
        return Product3DModelPublicSerializer(model).data


class CategoryWithProductsPublicSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "description", "image", "products"]
        read_only_fields = fields

    def get_products(self, category):
        available = [p for p in category.products.all() if p.is_available]
        return ProductPublicSerializer(available, many=True).data
