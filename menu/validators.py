import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image_file(image_field):
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


def validate_3d_model_file(file_field):
    extension = os.path.splitext(file_field.name)[1].lstrip(".").lower()
    if extension not in settings.ALLOWED_3D_MODEL_EXTENSIONS:
        raise ValidationError(
            f"Unsupported 3D model format '.{extension}'. Allowed formats: "
            f"{', '.join(settings.ALLOWED_3D_MODEL_EXTENSIONS)}."
        )

    max_size = settings.MAX_3D_MODEL_UPLOAD_SIZE_MB * 1024 * 1024
    if file_field.size > max_size:
        raise ValidationError(
            f"3D model file too large. Maximum allowed size is "
            f"{settings.MAX_3D_MODEL_UPLOAD_SIZE_MB} MB."
        )
