from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from restaurants.models import Restaurant
from .validators import validate_3d_model_file, validate_image_file


def category_image_path(instance, filename):
    return f"restaurants/{instance.restaurant_id}/categories/{filename}"


def product_image_path(instance, filename):
    return f"restaurants/{instance.restaurant_id}/products/{filename}"


def product_3d_model_path(instance, filename):
    return f"restaurants/{instance.product.restaurant_id}/products/{instance.product_id}/3d/{filename}"


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=category_image_path, blank=True, null=True, validators=[validate_image_file]
    )
    sort_order = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"
        constraints = [
            models.CheckConstraint(check=models.Q(sort_order__gte=0), name="category_sort_order_gte_0"),
        ]

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class Product(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    image = models.ImageField(
        upload_to=product_image_path, blank=True, null=True, validators=[validate_image_file]
    )
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name="product_price_gte_0"),
            models.CheckConstraint(check=models.Q(sort_order__gte=0), name="product_sort_order_gte_0"),
        ]

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

    def clean(self):
        if self.category_id and self.restaurant_id and self.category.restaurant_id != self.restaurant_id:
            raise ValidationError("Product's restaurant must match its category's restaurant.")

    def save(self, *args, **kwargs):
        self.full_clean(exclude=[f.name for f in self._meta.fields if f.name not in ("category", "restaurant")])
        super().save(*args, **kwargs)


class Product3DModel(models.Model):
    class Format(models.TextChoices):
        GLB = "glb", "GLB"
        GLTF = "gltf", "glTF"
        FBX = "fbx", "FBX"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="model_3d")
    model_file = models.FileField(
        upload_to=product_3d_model_path, blank=True, null=True, validators=[validate_3d_model_file]
    )
    model_url = models.URLField(blank=True)
    format = models.CharField(max_length=10, choices=Format.choices)
    is_ar_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"3D model for {self.product.name}"

    def clean(self):
        if not self.model_file and not self.model_url:
            raise ValidationError("Either model_file or model_url must be provided.")
