from django.conf import settings
from django.db import models
from django.utils.text import slugify

from .validators import validate_image_file


def restaurant_logo_path(instance, filename):
    return f"restaurants/{instance.slug or 'unsaved'}/logo/{filename}"


def restaurant_cover_path(instance, filename):
    return f"restaurants/{instance.slug or 'unsaved'}/cover/{filename}"


class Restaurant(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="restaurants"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to=restaurant_logo_path, blank=True, null=True, validators=[validate_image_file]
    )
    cover_image = models.ImageField(
        upload_to=restaurant_cover_path, blank=True, null=True, validators=[validate_image_file]
    )
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Restaurant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"
        return slug
