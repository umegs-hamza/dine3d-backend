from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Wrap DRF's default error responses in the platform's standard envelope."""
    response = exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(response.data, dict) and "detail" in response.data and len(response.data) == 1:
        message = str(response.data["detail"])
        errors = {}
    else:
        message = "Request failed validation."
        errors = response.data if isinstance(response.data, (dict, list)) else {}

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
