from rest_framework import serializers

from .models import Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "owner",
            "owner_email",
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
        read_only_fields = ["id", "owner", "slug", "created_at", "updated_at"]


class RestaurantPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "name", "slug", "description", "logo", "cover_image", "city"]
        read_only_fields = fields
