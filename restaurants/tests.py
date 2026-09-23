from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from restaurants.models import Restaurant


class RestaurantListTests(APITestCase):
    """Restaurants are list-only via the API (create/retrieve/update/destroy
    are not exposed) — managed through Django Admin or the seed command instead."""

    def setUp(self):
        self.owner_a = User.objects.create_user(email="ownera@example.com", password="StrongPass123")
        self.owner_b = User.objects.create_user(email="ownerb@example.com", password="StrongPass123")
        self.admin = User.objects.create_user(
            email="admin@example.com", password="StrongPass123", role=User.Role.ADMIN
        )
        self.restaurant_b = Restaurant.objects.create(name="Restaurant B", owner=self.owner_b)

    def test_admin_sees_all_restaurants_in_list(self):
        Restaurant.objects.create(name="Restaurant A", owner=self.owner_a)
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_owner_only_sees_own_restaurants_in_list(self):
        Restaurant.objects.create(name="Restaurant A", owner=self.owner_a)
        self.client.force_authenticate(self.owner_a)
        response = self.client.get("/api/v1/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_unauthenticated_cannot_access_restaurants(self):
        response = self.client.get("/api/v1/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_endpoint_is_not_exposed(self):
        self.client.force_authenticate(self.owner_a)
        response = self.client.post("/api/v1/restaurants/", {"name": "New Restaurant"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_detail_endpoint_is_not_exposed(self):
        self.client.force_authenticate(self.owner_b)
        response = self.client.get(f"/api/v1/restaurants/{self.restaurant_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_endpoint_is_not_exposed(self):
        self.client.force_authenticate(self.owner_b)
        response = self.client.patch(f"/api/v1/restaurants/{self.restaurant_b.id}/", {"name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_endpoint_is_not_exposed(self):
        self.client.force_authenticate(self.owner_b)
        response = self.client.delete(f"/api/v1/restaurants/{self.restaurant_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Restaurant.objects.filter(pk=self.restaurant_b.id).exists())
