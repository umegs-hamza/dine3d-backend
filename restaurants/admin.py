from django.contrib import admin

from .models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "city", "is_published", "is_active", "created_at"]
    list_filter = ["is_published", "is_active", "city"]
    search_fields = ["name", "city", "owner__email"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
