from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from admin_api.views import AdminDashboardView
from menu.views import Product3DModelView, PublicRestaurantMenuView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("api/v1/admin/", include("admin_api.urls")),
    path("api/v1/restaurants/", include("restaurants.urls")),
    path("api/v1/", include("menu.urls")),
    path(
        "api/v1/products/<int:product_id>/3d/",
        Product3DModelView.as_view(),
        name="product-3d-model",
    ),
    path(
        "api/v1/public/restaurants/<slug:slug>/",
        PublicRestaurantMenuView.as_view(),
        name="public-restaurant-menu",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
