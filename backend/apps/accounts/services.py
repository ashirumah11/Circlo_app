"""
Business logic services for Accounts and Authentication.
Reusable across REST API endpoints and server-rendered web views.
"""
from typing import Any, Dict, Optional, Tuple
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthService:
    """Handles core authentication operations and token lifecycle."""

    @staticmethod
    def register_user(
        email: str,
        username: str,
        full_name: str,
        password: str,
        **extra_fields
    ) -> Tuple[User, Dict[str, str]]:
        """
        Creates a new user and generates initial JWT tokens.
        """
        user = User.objects.create_user(
            email=email,
            username=username,
            full_name=full_name,
            password=password,
            **extra_fields
        )
        tokens = AuthService.generate_tokens_for_user(user)
        return user, tokens

    @staticmethod
    def authenticate_user(
        identifier: str,
        password: str,
        request=None
    ) -> Tuple[Optional[User], Optional[Dict[str, str]]]:
        """
        Authenticates a user by email or username and issues JWT tokens.
        """
        user = authenticate(request=request, username=identifier, password=password)
        if not user:
            return None, None

        tokens = AuthService.generate_tokens_for_user(user)
        return user, tokens

    @staticmethod
    def generate_tokens_for_user(user: User) -> Dict[str, str]:
        """
        Generates access and refresh JWT tokens for a given user.
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def blacklist_refresh_token(refresh_token_str: str) -> bool:
        """
        Blacklists a refresh token upon logout.
        """
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
            return True
        except Exception:
            return False

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> None:
        """
        Verifies current password and sets a new one.
        """
        if not user.check_password(current_password):
            raise ValidationError({'current_password': 'The current password you entered is incorrect.'})
        
        user.set_password(new_password)
        user.save(update_fields=['password'])

    @staticmethod
    def generate_password_reset_token(email: str) -> Optional[Tuple[User, str, str]]:
        """
        Finds user by email and creates uidb64 and password reset token.
        """
        try:
            user = User.objects.get(email__iexact=email.strip())
        except User.DoesNotExist:
            return None

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return user, uid, token

    @staticmethod
    def reset_password_with_token(uidb64: str, token: str, new_password: str) -> User:
        """
        Validates token and uidb64, then updates user's password.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({'token': 'Invalid or expired password reset link.'})

        if not default_token_generator.check_token(user, token):
            raise ValidationError({'token': 'Invalid or expired password reset link.'})

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return user


class ProfileService:
    """Handles profile queries and updates."""

    @staticmethod
    def get_profile_by_id_or_username(identifier: str) -> Optional[User]:
        """
        Finds a user by primary key or by username.
        """
        if identifier.isdigit():
            user = User.objects.filter(pk=int(identifier)).first()
            if user:
                return user
        
        clean_handle = identifier.lstrip('@').lower()
        return User.objects.filter(username__iexact=clean_handle).first()

    @staticmethod
    def update_profile(user: User, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> User:
        """
        Updates editable profile attributes with validation.
        """
        allowed_fields = ['full_name', 'bio', 'website', 'location', 'is_private']
        update_fields = []

        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
                update_fields.append(field)

        if files and 'profile_picture' in files:
            user.profile_picture = files['profile_picture']
            update_fields.append('profile_picture')

        if update_fields:
            update_fields.append('updated_at')
            user.full_name = user.full_name.strip()
            user.clean()
            user.save(update_fields=update_fields)

        return user
