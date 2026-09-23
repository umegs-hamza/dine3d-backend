from django.contrib import admin

from .models import Category, Product, Product3DModel


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "sort_order", "is_active", "created_at"]
    list_filter = ["is_active", "restaurant"]
    search_fields = ["name", "restaurant__name"]


class Product3DModelInline(admin.StackedInline):
    model = Product3DModel
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "category", "price", "is_available", "is_featured", "created_at"]
    list_filter = ["is_available", "is_featured", "restaurant"]
    search_fields = ["name", "restaurant__name", "category__name"]
    inlines = [Product3DModelInline]


@admin.register(Product3DModel)
class Product3DModelAdmin(admin.ModelAdmin):
    list_display = ["product", "format", "is_ar_enabled", "created_at"]
    list_filter = ["format", "is_ar_enabled"]
    search_fields = ["product__name"]
