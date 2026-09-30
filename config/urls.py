from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from admin_api.views import AdminDashboardView
from menu.views import Product3DModelView, PublicRestaurantListView, PublicRestaurantMenuView

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
        "api/v1/public/restaurants/",
        PublicRestaurantListView.as_view(),
        name="public-restaurant-list",
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
elif not settings.USE_GCS:
    # Django's static() helper (above) refuses to serve anything outside
    # DEBUG, and there is no nginx/reverse-proxy in front of gunicorn here
    # (see the backend Dockerfile) to serve MEDIA_ROOT some other way. With
    # USE_GCS off, uploaded images and 3D model files are stored on local
    # disk, so without this route every uploaded file 404s in production —
    # which is exactly why AR (fetching an uploaded .glb by URL) silently
    # failed to load anything. Wiring django.views.static.serve directly
    # bypasses that DEBUG guard; it's not as fast as a dedicated static file
    # server, but this app's media traffic doesn't need one, and it's far
    # better than uploads being unreachable outright. Switching USE_GCS=True
    # remains the more scalable option.
    urlpatterns += [
        re_path(
            rf"^{settings.MEDIA_URL.lstrip('/')}(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
