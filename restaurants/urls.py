from rest_framework.routers import DefaultRouter

from .views import RestaurantViewSet

app_name = "restaurants"

router = DefaultRouter()
router.register("", RestaurantViewSet, basename="restaurant")

urlpatterns = router.urls
