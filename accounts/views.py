from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from config.responses import error_response, success_response

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """Public registration endpoint. Always creates a RESTAURANT_OWNER account."""

    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response(
            data=UserSerializer(user).data,
            message="Registration successful.",
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticates a user and returns JWT access/refresh tokens."""

    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = serializer.get_tokens(user)
        return success_response(
            data={"user": UserSerializer(user).data, **tokens},
            message="Login successful.",
        )


class MeView(APIView):
    """Returns the authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data=UserSerializer(request.user).data)
