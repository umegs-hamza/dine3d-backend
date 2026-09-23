import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from menu.models import Category, Product, Product3DModel
from restaurants.models import Restaurant


def make_test_image():
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.read(), content_type="image/jpeg")


class CategoryTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongPass123")
        self.restaurant = Restaurant.objects.create(name="My Restaurant", owner=self.owner)

    def test_owner_can_create_category(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/categories/", {"restaurant": self.restaurant.id, "name": "Burgers"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_cannot_create_category_for_others_restaurant(self):
        other_owner = User.objects.create_user(email="other@example.com", password="StrongPass123")
        other_restaurant = Restaurant.objects.create(name="Other", owner=other_owner)
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/categories/", {"restaurant": other_restaurant.id, "name": "Burgers"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_image_upload(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/categories/",
            {"restaurant": self.restaurant.id, "name": "Burgers", "image": make_test_image()},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["image"])


class ProductTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongPass123")
        self.restaurant = Restaurant.objects.create(name="My Restaurant", owner=self.owner)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Burgers")

    def test_owner_can_create_product(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/products/",
            {
                "restaurant": self.restaurant.id,
                "category": self.category.id,
                "name": "Zinger Burger",
                "price": "550.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_product_restaurant_must_match_category_restaurant(self):
        other_owner = User.objects.create_user(email="other@example.com", password="StrongPass123")
        other_restaurant = Restaurant.objects.create(name="Other", owner=other_owner)
        other_category = Category.objects.create(restaurant=self.restaurant, name="Drinks")
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/products/",
            {
                "restaurant": other_restaurant.id,
                "category": other_category.id,
                "name": "Bad Product",
                "price": "100.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_image_upload(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/products/",
            {
                "restaurant": self.restaurant.id,
                "category": self.category.id,
                "name": "Zinger Burger",
                "price": "550.00",
                "image": make_test_image(),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["image"])

    def test_owner_cannot_access_other_owners_products(self):
        other_owner = User.objects.create_user(email="other@example.com", password="StrongPass123")
        other_restaurant = Restaurant.objects.create(name="Other", owner=other_owner)
        other_category = Category.objects.create(restaurant=other_restaurant, name="Drinks")
        other_product = Product.objects.create(
            restaurant=other_restaurant, category=other_category, name="Secret", price="100.00"
        )
        self.client.force_authenticate(self.owner)
        response = self.client.get(f"/api/v1/products/{other_product.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class Product3DModelTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongPass123")
        self.restaurant = Restaurant.objects.create(name="My Restaurant", owner=self.owner)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Burgers")
        self.product = Product.objects.create(
            restaurant=self.restaurant, category=self.category, name="Zinger Burger", price="550.00"
        )

    def test_owner_can_upload_3d_model(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            f"/api/v1/products/{self.product.id}/3d/",
            {"model_url": "https://example.com/model.glb", "format": "glb", "is_ar_enabled": True},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product3DModel.objects.filter(product=self.product).exists())

    def test_3d_model_requires_file_or_url(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            f"/api/v1/products/{self.product.id}/3d/", {"format": "glb"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PublicMenuTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongPass123")
        self.restaurant = Restaurant.objects.create(
            name="Kabab House", owner=self.owner, is_published=True, is_active=True
        )
        self.category = Category.objects.create(restaurant=self.restaurant, name="Burgers")
        self.available_product = Product.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name="Zinger Burger",
            price="550.00",
            is_available=True,
        )
        self.unavailable_product = Product.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name="Sold Out Burger",
            price="600.00",
            is_available=False,
        )

    def test_public_menu_returns_published_restaurant(self):
        response = self.client.get(f"/api/v1/public/restaurants/{self.restaurant.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["restaurant"]["slug"], self.restaurant.slug)

    def test_public_menu_excludes_unavailable_products(self):
        response = self.client.get(f"/api/v1/public/restaurants/{self.restaurant.slug}/")
        product_names = [
            p["name"] for p in response.data["data"]["categories"][0]["products"]
        ]
        self.assertIn("Zinger Burger", product_names)
        self.assertNotIn("Sold Out Burger", product_names)

    def test_unpublished_restaurant_is_not_public(self):
        self.restaurant.is_published = False
        self.restaurant.save()
        response = self.client.get(f"/api/v1/public/restaurants/{self.restaurant.slug}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_menu_requires_no_authentication(self):
        response = self.client.get(f"/api/v1/public/restaurants/{self.restaurant.slug}/")
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
