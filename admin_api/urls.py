from rest_framework.routers import DefaultRouter

from .views import (
    AdminCategoryViewSet,
    AdminProduct3DModelViewSet,
    AdminProductViewSet,
    AdminRestaurantViewSet,
    AdminUserViewSet,
)

app_name = "admin_api"

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="admin-user")
router.register("restaurants", AdminRestaurantViewSet, basename="admin-restaurant")
router.register("categories", AdminCategoryViewSet, basename="admin-category")
router.register("products", AdminProductViewSet, basename="admin-product")
router.register("3d-models", AdminProduct3DModelViewSet, basename="admin-3d-model")

urlpatterns = router.urls
