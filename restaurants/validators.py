from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image_file(image_field):
    """Validates content type and file size for uploaded images."""
    content_type = getattr(image_field.file, "content_type", None)
    if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported image type '{content_type}'. Allowed types: "
            f"{', '.join(settings.ALLOWED_IMAGE_CONTENT_TYPES)}."
        )

    max_size = settings.MAX_IMAGE_UPLOAD_SIZE_MB * 1024 * 1024
    if image_field.size > max_size:
        raise ValidationError(
            f"Image file too large. Maximum allowed size is {settings.MAX_IMAGE_UPLOAD_SIZE_MB} MB."
        )
