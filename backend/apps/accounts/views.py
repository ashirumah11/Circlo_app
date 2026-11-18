from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from .services import AuthService, ProfileService

User = get_user_model()


class RegisterAPIView(APIView):
    """
    Public registration endpoint.
    Creates a new user account and returns JWT authentication tokens.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register new user account",
        description="Creates a new account with email, username, full name, and password.",
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                description="User registered successfully",
                response=UserProfileSerializer,
            ),
            400: OpenApiResponse(description="Validation error"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        tokens = AuthService.generate_tokens_for_user(user)
        user_data = UserProfileSerializer(user, context={'request': request}).data

        response = Response(
            {
                'message': 'Account created successfully.',
                'user': user_data,
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED
        )

        # Set secure HTTP-only cookie for refresh token
        response.set_cookie(
            key='circlo_refresh',
            value=tokens['refresh'],
            httponly=True,
            secure=not request.META.get('HTTP_HOST', '').startswith('localhost'),
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,
        )
        return response


class LoginAPIView(APIView):
    """
    User login endpoint.
    Authenticates using either email address or username and returns JWT tokens.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User login",
        description="Authenticates with email or username and password.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful"),
            401: OpenApiResponse(description="Invalid credentials"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data['password']

        user, tokens = AuthService.authenticate_user(
            identifier=identifier,
            password=password,
            request=request
        )

        if not user:
            return Response(
                {'detail': 'Invalid email/username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'This account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_data = UserProfileSerializer(user, context={'request': request}).data
        response = Response(
            {
                'message': 'Login successful.',
                'user': user_data,
                'tokens': tokens,
            },
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            key='circlo_refresh',
            value=tokens['refresh'],
            httponly=True,
            secure=not request.META.get('HTTP_HOST', '').startswith('localhost'),
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,
        )
        return response


class LogoutAPIView(APIView):
    """
    Logout endpoint.
    Blacklists the refresh token and clears auth cookies.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="User logout",
        description="Invalidates the provided refresh token and clears cookies.",
        responses={200: OpenApiResponse(description="Logged out successfully")}
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh') or request.COOKIES.get('circlo_refresh')

        if refresh_token:
            AuthService.blacklist_refresh_token(refresh_token)

        response = Response(
            {'message': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('circlo_refresh')
        return response


class CurrentUserAPIView(APIView):
    """
    Authenticated user endpoint (/api/v1/auth/me/).
    Retrieves or updates the currently authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get current user profile",
        responses={200: UserProfileSerializer}
    )
    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update current user profile",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    def patch(self, request, *args, **kwargs):
        user = ProfileService.update_profile(
            user=request.user,
            data=request.data,
            files=request.FILES
        )
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    Endpoint for authenticated users to change their password.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change password",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Validation error"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.change_password(
                user=request.user,
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password']
            )
        except DjangoValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        # Issue fresh tokens so the user is not unexpectedly locked out
        tokens = AuthService.generate_tokens_for_user(request.user)
        return Response(
            {
                'message': 'Password has been updated successfully.',
                'tokens': tokens,
            },
            status=status.HTTP_200_OK
        )


class PasswordResetRequestAPIView(APIView):
    """
    Endpoint to initiate password reset via email.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request password reset link",
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description="Reset link dispatched if email exists")}
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        result = AuthService.generate_password_reset_token(email)

        if result:
            user, uid, token = result
            # In development, console email backend prints the reset URL
            reset_url = f"/auth/password-reset-confirm/{uid}/{token}/"
            # Return URL in dev mode for easy testing
            return Response(
                {
                    'message': 'If an account exists with that email, a password reset link has been dispatched.',
                    'dev_reset_url': reset_url,
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {'message': 'If an account exists with that email, a password reset link has been dispatched.'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmAPIView(APIView):
    """
    Endpoint to confirm and apply new password using reset token.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Confirm password reset",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successful"),
            400: OpenApiResponse(description="Invalid or expired token"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.reset_password_with_token(
                uidb64=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            )
        except DjangoValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'message': 'Password has been reset successfully. You may now log in with your new password.'},
            status=status.HTTP_200_OK
        )
