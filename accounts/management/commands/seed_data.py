import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from accounts.models import User
from menu.models import Category, Product, Product3DModel
from restaurants.models import Restaurant

RESTAURANT_SLUG = "burger-house"

OWNER_EMAIL = "owner@burgerhouse.com"
OWNER_PASSWORD = "Owner@12345"

CATEGORIES = [
    {
        "name": "Burgers",
        "description": "Delicious crispy and grilled burgers prepared with fresh ingredients.",
    },
    {
        "name": "Pizza",
        "description": "Freshly baked pizzas with delicious toppings and melted cheese.",
    },
    {"name": "Fries", "description": "Crispy fries and loaded fries."},
    {"name": "Drinks", "description": "Refreshing cold drinks and beverages."},
    {"name": "Desserts", "description": "Sweet desserts and shakes."},
]

PRODUCTS = [
    # (category name, name, description, price, is_available, is_featured)
    ("Burgers", "Zinger Burger", "Crispy chicken fillet, fresh lettuce, cheese and special burger sauce.", "550", True, True),
    ("Burgers", "Cheese Burger", "Juicy beef patty, cheddar cheese, lettuce, tomato and special sauce.", "650", True, True),
    ("Burgers", "BBQ Chicken Burger", "Grilled chicken fillet, BBQ sauce, cheese and fresh vegetables.", "700", True, False),
    ("Burgers", "Double Beef Burger", "Two juicy beef patties with cheddar cheese and special burger sauce.", "850", True, True),
    ("Pizza", "Chicken Fajita Pizza", "Chicken, capsicum, onion, mozzarella cheese and fajita sauce.", "1200", True, True),
    ("Pizza", "Chicken BBQ Pizza", "BBQ chicken, onion, capsicum and mozzarella cheese.", "1300", True, True),
    ("Pizza", "Cheese Pizza", "Classic pizza loaded with mozzarella and cheddar cheese.", "1000", True, False),
    ("Pizza", "Pepperoni Pizza", "Mozzarella cheese and delicious pepperoni toppings.", "1400", False, False),
    ("Fries", "Regular Fries", "Golden crispy potato fries seasoned with special spices.", "250", True, False),
    ("Fries", "Loaded Cheese Fries", "Crispy fries topped with creamy cheese sauce.", "450", True, True),
    ("Fries", "Masala Fries", "Crispy fries tossed with our special masala seasoning.", "300", True, False),
    ("Drinks", "Coca Cola", "Chilled Coca Cola.", "120", True, False),
    ("Drinks", "Fresh Lime", "Freshly prepared sweet and sour lime drink.", "180", True, False),
    ("Drinks", "Mint Margarita", "Refreshing mint and lemon drink served chilled.", "250", True, True),
    ("Desserts", "Chocolate Brownie", "Soft chocolate brownie served with chocolate sauce.", "350", True, False),
    ("Desserts", "Chocolate Shake", "Creamy chocolate milkshake with rich chocolate flavor.", "400", True, True),
    ("Desserts", "Oreo Shake", "Creamy vanilla shake blended with Oreo cookies.", "450", True, True),
]

# Products that get a demo Product3DModel record.
PRODUCTS_WITH_3D = ["Zinger Burger", "Cheese Burger", "Chicken Fajita Pizza", "Chocolate Shake"]


def make_placeholder_image(label, size, color):
    """Generates a simple in-memory JPEG placeholder with the label drawn on it."""
    image = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", size=max(18, size[0] // 20))
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    position = ((size[0] - text_w) / 2, (size[1] - text_h) / 2)
    draw.text(position, label, fill="white", font=font)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return ContentFile(buffer.read())


def slugify_filename(name):
    return name.lower().replace(" ", "_")


class Command(BaseCommand):
    help = "Seeds (or clears) demo data for exactly one restaurant: Burger House."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove only the Burger House demo restaurant and its related data.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()
            return
        self._seed()

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------
    @transaction.atomic
    def _clear(self):
        deleted, _ = Restaurant.objects.filter(slug=RESTAURANT_SLUG).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS("Burger House demo restaurant and related data removed."))
        else:
            self.stdout.write(self.style.WARNING("No Burger House demo restaurant found. Nothing to remove."))

    # ------------------------------------------------------------------
    # Seed
    # ------------------------------------------------------------------
    @transaction.atomic
    def _seed(self):
        owner = self._create_owner()
        restaurant = self._create_restaurant(owner)
        categories = self._create_categories(restaurant)
        products = self._create_products(restaurant, categories)
        model_count = self._create_3d_models(products)

        self.stdout.write(self.style.SUCCESS("\n========================================"))
        self.stdout.write(self.style.SUCCESS("BURGER HOUSE DEMO DATA CREATED"))
        self.stdout.write(self.style.SUCCESS("========================================\n"))
        self.stdout.write(f"Owner:\n{OWNER_EMAIL}\n")
        self.stdout.write(f"Password:\n{OWNER_PASSWORD}\n")
        self.stdout.write(f"Restaurant:\n{restaurant.name}\n")
        self.stdout.write(f"Categories:\n{len(categories)}\n")
        self.stdout.write(f"Products:\n{len(products)}\n")
        self.stdout.write(f"3D Model Records:\n{model_count}\n")
        self.stdout.write(self.style.SUCCESS("========================================"))

    def _create_owner(self):
        owner, created = User.objects.get_or_create(
            email=OWNER_EMAIL,
            defaults={
                "first_name": "Ali",
                "last_name": "Khan",
                "role": User.Role.RESTAURANT_OWNER,
            },
        )
        if created:
            owner.set_password(OWNER_PASSWORD)
            owner.save()
            self.stdout.write(self.style.SUCCESS(f"Created restaurant owner: {owner.email}"))
        else:
            self.stdout.write(f"Restaurant owner already exists: {owner.email}")
        return owner

    def _create_restaurant(self, owner):
        restaurant, created = Restaurant.objects.update_or_create(
            slug=RESTAURANT_SLUG,
            defaults={
                "owner": owner,
                "name": "Burger House",
                "description": (
                    "A modern fast-food restaurant serving burgers, pizzas, fries, "
                    "drinks and desserts."
                ),
                "city": "Gujranwala",
                "address": "Main GT Road, Gujranwala",
                "phone": "03001234567",
                "is_published": True,
                "is_active": True,
            },
        )
        if not restaurant.logo:
            restaurant.logo.save(
                "restaurant_logo.jpg",
                make_placeholder_image("Burger House Logo", (500, 500), "#8B0000"),
                save=False,
            )
        if not restaurant.cover_image:
            restaurant.cover_image.save(
                "restaurant_cover.jpg",
                make_placeholder_image("Burger House", (1400, 600), "#D2691E"),
                save=False,
            )
        restaurant.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created restaurant: {restaurant.name}"))
        else:
            self.stdout.write(f"Restaurant already existed, updated: {restaurant.name}")
        return restaurant

    def _create_categories(self, restaurant):
        categories = {}
        for i, cat_data in enumerate(CATEGORIES):
            category, created = Category.objects.update_or_create(
                restaurant=restaurant,
                name=cat_data["name"],
                defaults={"description": cat_data["description"], "sort_order": i, "is_active": True},
            )
            categories[category.name] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {category.name}"))
            else:
                self.stdout.write(f"Category already existed, updated: {category.name}")
        return categories

    def _create_products(self, restaurant, categories):
        products = {}
        for i, (cat_name, name, description, price, is_available, is_featured) in enumerate(PRODUCTS):
            category = categories[cat_name]
            product, created = Product.objects.update_or_create(
                restaurant=restaurant,
                category=category,
                name=name,
                defaults={
                    "description": description,
                    "price": price,
                    "is_available": is_available,
                    "is_featured": is_featured,
                    "sort_order": i,
                },
            )
            if not product.image:
                filename = f"{slugify_filename(name)}.jpg"
                product.image.save(
                    filename, make_placeholder_image(name, (800, 600), "#556B2F"), save=False
                )
                product.save()

            products[name] = product
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {product.name}"))
            else:
                self.stdout.write(f"Product already existed, updated: {product.name}")
        return products

    def _create_3d_models(self, products):
        count = 0
        for name in PRODUCTS_WITH_3D:
            product = products[name]
            slug = slugify_filename(name)
            _, created = Product3DModel.objects.update_or_create(
                product=product,
                defaults={
                    "model_url": f"https://example.com/demo/{slug}.glb",
                    "format": Product3DModel.Format.GLB,
                    "is_ar_enabled": True,
                },
            )
            count += 1
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created 3D model record for: {product.name}"))
            else:
                self.stdout.write(f"3D model record already existed, updated: {product.name}")
        return count
