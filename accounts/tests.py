from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class RegistrationTests(APITestCase):
    def test_register_creates_restaurant_owner(self):
        url = reverse("accounts:register")
        payload = {
            "email": "newowner@example.com",
            "password": "StrongPass123",
            "first_name": "New",
            "last_name": "Owner",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newowner@example.com")
        self.assertEqual(user.role, User.Role.RESTAURANT_OWNER)

    def test_register_cannot_set_admin_role(self):
        url = reverse("accounts:register")
        payload = {
            "email": "wannabeadmin@example.com",
            "password": "StrongPass123",
            "role": "ADMIN",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="wannabeadmin@example.com")
        self.assertEqual(user.role, User.Role.RESTAURANT_OWNER)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="StrongPass123")

    def test_login_returns_jwt_tokens(self):
        url = reverse("accounts:login")
        response = self.client.post(url, {"email": "owner@example.com", "password": "StrongPass123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

    def test_login_invalid_credentials(self):
        url = reverse("accounts:login")
        response = self.client.post(url, {"email": "owner@example.com", "password": "wrong"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="StrongPass123")

    def test_me_requires_authentication(self):
        url = reverse("accounts:me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile_when_authenticated(self):
        self.client.force_authenticate(self.user)
        url = reverse("accounts:me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "owner@example.com")
