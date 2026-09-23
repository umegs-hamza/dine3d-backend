from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from menu.models import Category, Product, Product3DModel
from restaurants.models import Restaurant


class AdminApiTestBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", password="StrongPass123", role=User.Role.ADMIN
        )
        self.owner_a = User.objects.create_user(email="ownera@example.com", password="StrongPass123")
        self.owner_b = User.objects.create_user(email="ownerb@example.com", password="StrongPass123")

        self.restaurant_a = Restaurant.objects.create(
            name="Restaurant A", owner=self.owner_a, is_published=True, is_active=True
        )
        self.restaurant_b = Restaurant.objects.create(
            name="Restaurant B", owner=self.owner_b, is_published=False, is_active=True
        )

        self.category_a = Category.objects.create(restaurant=self.restaurant_a, name="Burgers")
        self.product_a = Product.objects.create(
            restaurant=self.restaurant_a,
            category=self.category_a,
            name="Zinger Burger",
            price=Decimal("550.00"),
            is_available=True,
        )
        self.product_3d = Product3DModel.objects.create(
            product=self.product_a, model_url="https://example.com/demo/zinger.glb", format="glb"
        )


class AdminLoginAndDashboardTests(AdminApiTestBase):
    def test_admin_login(self):
        response = self.client.post(
            "/api/v1/auth/login/", {"email": "admin@example.com", "password": "StrongPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["user"]["role"], "ADMIN")

    def test_admin_dashboard_counts(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/admin/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["total_users"], 3)
        self.assertEqual(data["total_restaurants"], 2)
        self.assertEqual(data["published_restaurants"], 1)
        self.assertEqual(data["unpublished_restaurants"], 1)
        self.assertEqual(data["total_categories"], 1)
        self.assertEqual(data["total_products"], 1)
        self.assertEqual(data["available_products"], 1)
        self.assertEqual(data["total_3d_models"], 1)

    def test_dashboard_requires_admin_role(self):
        self.client.force_authenticate(self.owner_a)
        response = self.client.get("/api/v1/admin/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/api/v1/admin/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminRestaurantApiTests(AdminApiTestBase):
    def test_admin_can_list_restaurants(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/admin/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_admin_can_view_restaurant(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/v1/admin/restaurants/{self.restaurant_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Restaurant B")

    def test_admin_can_update_restaurant(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/admin/restaurants/{self.restaurant_b.id}/", {"is_published": True}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.restaurant_b.refresh_from_db()
        self.assertTrue(self.restaurant_b.is_published)

    def test_admin_can_delete_restaurant(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/v1/admin/restaurants/{self.restaurant_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Restaurant.objects.filter(pk=self.restaurant_b.id).exists())

    def test_restaurant_owner_cannot_access_admin_restaurants_api(self):
        self.client.force_authenticate(self.owner_a)
        response = self.client.get("/api/v1/admin/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restaurant_owner_cannot_delete_via_admin_api(self):
        self.client.force_authenticate(self.owner_b)
        response = self.client.delete(f"/api/v1/admin/restaurants/{self.restaurant_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Restaurant.objects.filter(pk=self.restaurant_a.id).exists())

    def test_anonymous_cannot_access_admin_restaurants_api(self):
        response = self.client.get("/api/v1/admin/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminUserApiTests(AdminApiTestBase):
    def test_admin_can_list_users(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_admin_can_deactivate_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f"/api/v1/admin/users/{self.owner_a.id}/", {"is_active": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner_a.refresh_from_db()
        self.assertFalse(self.owner_a.is_active)

    def test_admin_cannot_change_user_password_field(self):
        original_password = self.owner_a.password
        self.client.force_authenticate(self.admin)
        self.client.patch(f"/api/v1/admin/users/{self.owner_a.id}/", {"password": "hacked123"})
        self.owner_a.refresh_from_db()
        self.assertEqual(self.owner_a.password, original_password)

    def test_restaurant_owner_cannot_access_admin_users_api(self):
        self.client.force_authenticate(self.owner_a)
        response = self.client.get("/api/v1/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_access_admin_users_api(self):
        response = self.client.get("/api/v1/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminCategoryProductModelApiTests(AdminApiTestBase):
    def test_admin_can_list_categories(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/admin/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["products_count"], 1)

    def test_admin_can_list_products(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/admin/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(response.data["results"][0]["has_3d_model"])

    def test_admin_can_list_3d_models(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/admin/3d-models/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["format"], "glb")

    def test_owner_cannot_access_admin_categories_products_3d_apis(self):
        self.client.force_authenticate(self.owner_a)
        for url in ("/api/v1/admin/categories/", "/api/v1/admin/products/", "/api/v1/admin/3d-models/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, url)


class OwnerOwnDataAccessTests(AdminApiTestBase):
    """Confirms the existing owner-scoped (non-admin) endpoints still isolate
    owners correctly — unaffected by adding the /admin/ namespace."""

    def test_owner_can_access_own_restaurant_data(self):
        self.client.force_authenticate(self.owner_a)
        response = self.client.get(f"/api/v1/products/?restaurant={self.restaurant_a.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_owner_cannot_access_another_owners_restaurant_data(self):
        self.client.force_authenticate(self.owner_a)
        response = self.client.get(f"/api/v1/products/{self.product_a.id}/")
        # product_a belongs to restaurant_a which owner_a owns, so re-check with owner_b
        self.client.force_authenticate(self.owner_b)
        response = self.client.get(f"/api/v1/products/{self.product_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
